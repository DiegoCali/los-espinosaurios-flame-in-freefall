import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = '/home/ponche/.cache/puppeteer/chrome/linux-157.0.8103.50/chrome-linux64/chrome';

async function zoomIntoACME(nodeId, outPrefix) {
  const url = `https://www.figma.com/design/Uku1QlSTwB6PVpm5ikM5c8/Spinosaurios-Research-Hub?node-id=${encodeURIComponent(nodeId)}`;
  const port = 9333;
  const chrome = spawn(CHROME_PATH, [
    '--headless=new',
    '--no-sandbox',
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader',
    '--disable-gpu-sandbox',
    `--remote-debugging-port=${port}`,
    '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    '--window-size=1920,1080',
    `--user-data-dir=/tmp/figma-profile-zoom`,
    'about:blank'
  ]);

  try {
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 300));
      try {
        const res = await fetch(`http://127.0.0.1:${port}/json/version`);
        if (res.ok) break;
      } catch (e) {}
    }

    const newTargetRes = await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' });
    const target = await newTargetRes.json();
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    let id = 1;
    const callbacks = new Map();
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && callbacks.has(msg.id)) {
        callbacks.get(msg.id)(msg);
        callbacks.delete(msg.id);
      }
    };

    function send(method, params = {}) {
      return new Promise((resolve) => {
        const msgId = id++;
        callbacks.set(msgId, resolve);
        ws.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    await send('Runtime.enable');
    await send('Page.enable');
    await send('DOM.enable');

    console.log('Waiting 22s for load...');
    await new Promise(r => setTimeout(r, 22000));

    // Dismiss bottom banner
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });

    // Focus on canvas by clicking at (960, 400)
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 960, y: 400, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 960, y: 400, button: 'left', clickCount: 1 });
    await new Promise(r => setTimeout(r, 500));

    // Double click to zoom in or Shift+2
    console.log('Dispatching Shift+2...');
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 8, key: 'Shift', code: 'ShiftLeft', windowsVirtualKeyCode: 16 });
    await send('Input.dispatchKeyEvent', { type: 'keyDown', modifiers: 8, key: '@', text: '2', code: 'Digit2', windowsVirtualKeyCode: 50 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 8, key: '@', code: 'Digit2', windowsVirtualKeyCode: 50 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 0, key: 'Shift', code: 'ShiftLeft', windowsVirtualKeyCode: 16 });
    await new Promise(r => setTimeout(r, 2000));

    // Also zoom in multiple times using Ctrl + MouseWheel at (960, 400)
    for (let z = 0; z < 15; z++) {
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: 960,
        y: 400,
        deltaX: 0,
        deltaY: -120,
        modifiers: 2 // Control
      });
    }
    await new Promise(r => setTimeout(r, 3000));

    // Capture screenshot
    let res = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(`${outPrefix}-zoom-close.png`, Buffer.from(res.result.data, 'base64'));
    console.log(`Saved ${outPrefix}-zoom-close.png`);

    // Let's also pan down
    for (let step = 1; step <= 6; step++) {
      // Pan down by dragging space+mouse or wheel
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: 960,
        y: 500,
        deltaX: 0,
        deltaY: 500,
        modifiers: 0
      });
      await new Promise(r => setTimeout(r, 1500));
      res = await send('Page.captureScreenshot', { format: 'png' });
      writeFileSync(`${outPrefix}-section-${step}.png`, Buffer.from(res.result.data, 'base64'));
      console.log(`Saved ${outPrefix}-section-${step}.png`);
    }

    ws.close();
  } finally {
    chrome.kill();
  }
}

zoomIntoACME(process.argv[2] || '326-27', process.argv[3] || '/tmp/figma-acme-close').catch(console.error);
