/**
 * 端口检测与冲突处理脚本
 * 检测指定端口是否被占用，如被占用则自动终止占用进程
 */
const { exec, spawn } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

const TARGET_PORT = process.env.PORT || 8081;

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
        return { pid: parseInt(pid, 10), line };
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
      `tasklist /FI "PID eq ${pid}" /FO CSV /NH`,
      { encoding: 'utf8', shell: 'cmd.exe' }
    );
    return stdout.trim();
  } catch {
    return null;
  }
}

async function killProcess(pid) {
  try {
    console.log(`正在尝试终止进程 PID: ${pid}...`);
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

  const processInfo = await findProcessByPort(TARGET_PORT);

  if (processInfo) {
    console.log(`检测到端口 ${TARGET_PORT} 已被占用`);
    console.log(`进程信息:`);
    console.log(`  PID: ${processInfo.pid}`);

    const processDetails = await getProcessInfo(processInfo.pid);
    if (processDetails) {
      console.log(`  进程详情: ${processDetails}`);
    }

    const killed = await killProcess(processInfo.pid);

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

  const serveProcess = spawn('vue-cli-service', ['serve'], {
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
