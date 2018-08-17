import os
import pytest
import subprocess
import testinfra

@pytest.fixture(scope='session')
def host(request):
    subprocess.check_call(['docker', 'build', '-t', 'radicale', '.'])
    docker_id = subprocess.check_output(['docker', 'run', '-d', 'radicale']).decode().strip()
    
    yield testinfra.get_host("docker://" + docker_id)
    
    # teardown
    subprocess.check_call(['docker', 'rm', '-f', docker_id])

def test_entrypoint(host):
    entrypoint = '/usr/local/bin/docker-entrypoint.sh'
    assert host.file(entrypoint).exists
    assert oct(host.file(entrypoint).mode) == '0o755'

def test_radicale_process(host):
    assert host.file('/proc/1/cmdline').content_string.replace('\x00','') == '/usr/bin/python3/usr/bin/radicale--config/config/config'

def test_radicale_version(host):
    assert host.run("/usr/bin/pip3 --disable-pip-version-check show radicale | grep Version | awk -F ' ' '{print $2}' | tr -d '\n'").stdout == os.environ.get('VERSION','2.1.9')

def test_radicale_port(host):
    assert host.socket("tcp://0.0.0.0:5232").is_listening

def test_radicale_user(host):
    assert host.user('radicale').uid == 2999
    assert host.user('radicale').gid == 2999

@pytest.mark.parametrize('package', [
    ('curl'),
    ('git'),
    ('shadow'),
    ('su-exec'),
])
def test_installed_dependencies(host, package):
    assert host.package(package).is_installed
