/**
 * 端口检测与冲突处理脚本
 * 检测指定端口是否被占用，如被占用则自动终止占用进程
 *
 * 注意：此脚本仅终止以下类型的进程：
 * - node.exe (Node.js 开发服务器)
 * - python.exe / pythonw.exe (Python 开发服务器)
 * - java.exe (Java 开发服务器)
 *
 * 不会终止系统关键进程或数据库进程
 */
const { exec, spawn } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

const TARGET_PORT = process.env.PORT || 9081;

const SAFE_TO_KILL_PROCESSES = [
  'node.exe',
  'python.exe',
  'pythonw.exe',
  'java.exe',
  'javaw.exe',
];

const SAFE_TO_KILL_PATTERNS = [
  /vue-cli-service/i,
  /node.*webpack/i,
  /npm.*dev/i,
  /python.*manage.*runserver/i,
  /python.*runserver/i,
  /django.*runserver/i,
  /uvicorn/i,
  /fastapi/i,
  /spring.*boot/i,
];

function isSafeToKill(processName, commandLine) {
  if (!processName) return false;

  if (SAFE_TO_KILL_PROCESSES.includes(processName.toLowerCase())) {
    if (commandLine) {
      for (const pattern of SAFE_TO_KILL_PATTERNS) {
        if (pattern.test(commandLine)) {
          return true;
        }
      }
      return false;
    }
    return true;
  }

  return false;
}

async function findProcessByPort(port) {
  try {
    const { stdout } = await execAsync(
      `netstat -ano | findstr :${port}`,
      { encoding: 'utf8', shell: 'cmd.exe' }
    );

    const lines = stdout.trim().split('\n').filter(line => line.includes(`:${port}`));

    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      const localAddress = parts[1];
      const state = parts[3];
      const pid = parts[4];

      if (localAddress && localAddress.includes(`:${port}`) && state === 'LISTENING' && pid && pid !== '0') {
        return parseInt(pid, 10);
      }
    }
    return null;
  } catch (error) {
    return null;
  }
}

async function getProcessInfo(pid) {
  try {
    const { stdout } = await execAsync(
      `wmic process where ProcessId=${pid} get Name,CommandLine /format:csv`,
      { encoding: 'utf8', shell: 'cmd.exe' }
    );
    return stdout.trim();
  } catch {
    try {
      const { stdout } = await execAsync(
        `tasklist /FI "PID eq ${pid}" /FO CSV /NH`,
        { encoding: 'utf8', shell: 'cmd.exe' }
      );
      return stdout.trim();
    } catch {
      return null;
    }
  }
}

async function killProcess(pid, processName, commandLine) {
  if (!isSafeToKill(processName, commandLine)) {
    console.log(`跳过终止 PID ${pid} (${processName}) - 不在白名单中`);
    console.log(`  如需终止，请手动处理: taskkill /PID ${pid} /F`);
    return false;
  }

  try {
    console.log(`正在尝试终止进程 PID: ${pid} (${processName})...`);
    await execAsync(`taskkill /PID ${pid} /F`, { shell: 'cmd.exe' });
    console.log(`成功终止进程 PID: ${pid}`);
    return true;
  } catch (error) {
    console.error(`终止进程失败: ${error.message}`);
    return false;
  }
}

async function waitForPortAvailable(port, maxWaitMs = 5000) {
  const startTime = Date.now();
  while (Date.now() - startTime < maxWaitMs) {
    const processInfo = await findProcessByPort(port);
    if (!processInfo) {
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  return false;
}

async function main() {
  console.log(`\n========================================`);
  console.log(`端口冲突检测脚本启动`);
  console.log(`目标端口: ${TARGET_PORT}`);
  console.log(`========================================\n`);

  const pid = await findProcessByPort(TARGET_PORT);

  if (pid) {
    console.log(`检测到端口 ${TARGET_PORT} 已被占用`);
    console.log(`进程 PID: ${pid}`);

    let processName = null;
    let commandLine = null;
    try {
      const wmicOutput = await execAsync(
        `wmic process where ProcessId=${pid} get Name,CommandLine /format:csv`,
        { encoding: 'utf8', shell: 'cmd.exe' }
      );
      const lines = wmicOutput.stdout.trim().split('\n').filter(l => l.trim() && !l.startsWith('Node'));
      if (lines.length > 0) {
        const line = lines[0];
        const parts = line.split(',');
        if (parts.length >= 2) {
          processName = parts[parts.length - 1].replace(/"/g, '').trim();
          commandLine = parts.slice(0, -1).join(',').replace(/^"+|"+$/g, '').trim();
        } else if (parts.length === 1) {
          processName = parts[0].replace(/"/g, '').trim();
        }
        console.log(`  进程名: ${processName}`);
        console.log(`  命令行: ${commandLine}`);
      }
    } catch (e) {
      console.log(`  无法获取进程详细信息`);
    }

    const killed = await killProcess(pid, processName, commandLine);

    if (!killed) {
      console.error(`\n无法终止占用端口的进程，请手动关闭后重试`);
      console.error(`或者修改 vue.config.js 中的端口配置\n`);
      process.exit(1);
    }

    console.log(`\n等待端口释放...`);
    const available = await waitForPortAvailable(TARGET_PORT);

    if (!available) {
      console.error(`\n端口未能及时释放，请稍后重试\n`);
      process.exit(1);
    }

    console.log(`端口 ${TARGET_PORT} 现已可用\n`);
  } else {
    console.log(`端口 ${TARGET_PORT} 当前未被占用\n`);
  }

  console.log(`启动开发服务器...\n`);

  const serveProcess = spawn('vite', [], {
    stdio: 'inherit',
    shell: true,
    env: { ...process.env, FORCE_COLOR: '1' }
  });

  serveProcess.on('error', (error) => {
    console.error(`启动失败: ${error.message}`);
    process.exit(1);
  });

  serveProcess.on('close', (code) => {
    process.exit(code || 0);
  });
}

main().catch((error) => {
  console.error(`脚本执行错误: ${error.message}`);
  process.exit(1);
});
