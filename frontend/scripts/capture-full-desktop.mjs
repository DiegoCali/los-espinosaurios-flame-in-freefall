import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = '/home/ponche/.cache/puppeteer/chrome/linux-157.0.8103.50/chrome-linux64/chrome';

async function captureRest(nodeId, outPrefix) {
  const url = `https://www.figma.com/design/Uku1QlSTwB6PVpm5ikM5c8/Spinosaurios-Research-Hub?node-id=${encodeURIComponent(nodeId)}`;
  const port = 9666;
  const width = 1920;
  const height = 1200;

  const chrome = spawn(CHROME_PATH, [
    '--headless=new',
    '--no-sandbox',
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader',
    '--disable-gpu-sandbox',
    `--remote-debugging-port=${port}`,
    '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    `--window-size=${width},${height}`,
    `--user-data-dir=/tmp/figma-profile-rest`,
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

    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });

    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: width / 2, y: height / 2, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: width / 2, y: height / 2, button: 'left', clickCount: 1 });
    await new Promise(r => setTimeout(r, 500));

    // Zoom in 9 ticks with Ctrl + wheel
    for (let i = 0; i < 9; i++) {
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: -120,
        modifiers: 2
      });
    }
    await new Promise(r => setTimeout(r, 1500));

    // Pan WAY up first to get Hero and Sections 01, 02
    console.log('Panning to absolute top (Hero)...');
    for (let i = 0; i < 20; i++) {
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: -800,
        modifiers: 0
      });
    }
    await new Promise(r => setTimeout(r, 2000));

    let res = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(`${outPrefix}-00-hero.png`, Buffer.from(res.result.data, 'base64'));
    console.log(`Saved ${outPrefix}-00-hero.png`);

    // Pan down slightly for section 01 & 02
    for (let step = 1; step <= 3; step++) {
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: 700,
        modifiers: 0
      });
      await new Promise(r => setTimeout(r, 1500));
      res = await send('Page.captureScreenshot', { format: 'png' });
      writeFileSync(`${outPrefix}-top-${step}.png`, Buffer.from(res.result.data, 'base64'));
      console.log(`Saved ${outPrefix}-top-${step}.png`);
    }

    // Now pan down to bottom sections (lab curve, table, limits, sources)
    console.log('Panning down to bottom sections...');
    for (let step = 1; step <= 6; step++) {
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: 900,
        modifiers: 0
      });
      await new Promise(r => setTimeout(r, 1500));
      res = await send('Page.captureScreenshot', { format: 'png' });
      writeFileSync(`${outPrefix}-bottom-${step}.png`, Buffer.from(res.result.data, 'base64'));
      console.log(`Saved ${outPrefix}-bottom-${step}.png`);
    }

    ws.close();
  } finally {
    chrome.kill();
  }
}

captureRest(process.argv[2] || '326-27', process.argv[3] || '/tmp/acme-full').catch(console.error);
