"""Cria/atualiza job local com o Jenkinsfile e executa builds reais de CI."""
import argparse
import json
from base64 import b64encode
from http.cookiejar import CookieJar
from pathlib import Path
from time import sleep
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

project = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--env-file', type=Path, default=project / '.env')
parser.add_argument('--count', type=int, default=10)
parser.add_argument('--url', default='http://127.0.0.1:8080')
args = parser.parse_args()
if args.count < 1:
    parser.error('--count deve ser positivo')
settings = dict(line.split('=', 1) for line in args.env_file.read_text().splitlines() if '=' in line)
auth = 'Basic ' + b64encode(('admin:' + settings['JENKINS_ADMIN_PASSWORD']).encode()).decode()
opener = build_opener(HTTPCookieProcessor(CookieJar()))
out = project / 'evidence' / 'live'
out.mkdir(parents=True, exist_ok=True)

def call(path, data=None, crumb=None, content_type=None):
    headers = {'Authorization': auth}
    if crumb:
        headers[crumb[0]] = crumb[1]
    if content_type:
        headers['Content-Type'] = content_type
    with opener.open(Request(args.url + path, data=data, headers=headers), timeout=30) as response:
        return response.read()

crumb_data = json.loads(call('/crumbIssuer/api/json'))
crumb = crumb_data['crumbRequestField'], crumb_data['crumb']
script = (project / 'Jenkinsfile').read_text(encoding='utf-8')
if ']]>' in script:
    raise ValueError('Jenkinsfile contém delimitador CDATA')
xml = f'''<flow-definition plugin="workflow-job">
<description>Laboratório local Carparts; Azure desabilitada.</description>
<keepDependencies>false</keepDependencies>
<properties><hudson.model.ParametersDefinitionProperty><parameterDefinitions>
<hudson.model.BooleanParameterDefinition><name>LAB_MODE</name><defaultValue>true</defaultValue></hudson.model.BooleanParameterDefinition>
<hudson.model.BooleanParameterDefinition><name>ENABLE_AZURE_DEPLOY</name><defaultValue>false</defaultValue></hudson.model.BooleanParameterDefinition>
</parameterDefinitions></hudson.model.ParametersDefinitionProperty></properties>
<definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps"><script><![CDATA[{script}]]></script><sandbox>true</sandbox></definition>
<triggers/><disabled>false</disabled></flow-definition>'''
job = '/job/carparts-lab'
try:
    call(job + '/api/json')
except HTTPError as error:
    if error.code != 404:
        raise
    call('/createItem?name=carparts-lab', xml.encode(), crumb, 'application/xml')
else:
    call(job + '/config.xml', xml.encode(), crumb, 'application/xml')

def last():
    try:
        return json.loads(call(job + '/lastBuild/api/json'))
    except HTTPError as error:
        if error.code == 404:
            return {'number': 0}
        raise

for _ in range(args.count):
    previous = last()['number']
    call(job + '/buildWithParameters?LAB_MODE=true&ENABLE_AZURE_DEPLOY=false', b'', crumb, 'application/x-www-form-urlencoded')
    for attempt in range(180):
        sleep(1)
        build = last()
        if build['number'] > previous and not build['building']:
            print(f"Build {build['number']}: {build['result']} ({build['duration']} ms)", flush=True)
            (out / f"console-{build['number']}.txt").write_bytes(call(job + f"/{build['number']}/consoleText"))
            if build['result'] != 'SUCCESS':
                raise RuntimeError('Build falhou; série interrompida')
            break
    else:
        raise TimeoutError('Build não terminou em 3 minutos')

builds = json.loads(call(job + '/api/json?tree=builds[number,result,timestamp,duration,building,url]'))
(out / 'builds.json').write_text(json.dumps(builds, ensure_ascii=False, indent=2), encoding='utf-8')
nodes = json.loads(call('/computer/api/json?tree=computer[displayName,offline,numExecutors,assignedLabels[name]]'))
(out / 'nodes.json').write_text(json.dumps(nodes, ensure_ascii=False, indent=2), encoding='utf-8')
latest = last()['number']
report = json.loads(call(job + f'/{latest}/testReport/api/json?tree=duration,failCount,passCount,skipCount'))
(out / f'test-report-{latest}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
artifact = json.loads(call(job + f'/{latest}/artifact/evidence/build.json'))
(out / f'build-artifact-{latest}.json').write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding='utf-8')
print('Evidência atualizada em', out)
