"""Session-only permission profile for the approved Mesh chat qualification.

The native proxy enforces an empty domain allowlist; only the existing fixture
Unix socket is added. This does not configure the user's Codex installation.
"""
import json
from pathlib import Path
import stat


def config_args(workspace, socket_path):
    work = Path(workspace).resolve(strict=True)
    socket = Path(socket_path).resolve(strict=True)
    if not stat.S_ISSOCK(socket.stat().st_mode):
        raise ValueError('Mesh permission requires an existing Unix socket')
    # Pass an inline TOML table: dotted -c keys split periods inside socket names.
    protected = ','.join(json.dumps(str(work / name)) + '="read"'
                         for name in ('.git', '.agents', '.claude', '.codex'))
    profile = ('permissions={taskspec_chat={extends=":workspace",filesystem={' +
               protected + '},network={enabled=true,domains={},'
               'allow_local_binding=false,allow_upstream_proxy=false,'
               'dangerously_allow_non_loopback_proxy=false,'
               'dangerously_allow_all_unix_sockets=false,unix_sockets={' +
               json.dumps(str(socket)) + '="allow"}}}}')
    return ['-c', 'default_permissions="taskspec_chat"', '-c', profile,
            '-c', 'features.network_proxy=true', '-c', 'approval_policy="never"']


def apply(argv, workspace, socket_path):
    result = list(argv)
    index = result.index('--sandbox')
    if result[index + 1] != 'workspace-write':
        raise ValueError('Only the qualification workspace profile may be extended')
    del result[index:index + 2]
    result[2:2] = config_args(workspace, socket_path)
    return result
