import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { IDisposable, DisposableDelegate } from '@lumino/disposable';
import { ISplashScreen } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';

import splashGif from '../style/logo-animated-fast.gif';
import '../style/base.css';

// Jupyter reference

const poweredByPlugin: JupyterFrontEndPlugin<void> = {
  id: 'custom-powered-by-label',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    const topBarObserver = new MutationObserver(() => {
      const topBar = document.getElementById('jp-top-bar');
      if (!topBar) {
        return;
      }
      const container = new Widget();
      container.node.innerHTML = `
        <a href="https://github.com/jupyterlab/jupyterlab"
           target="_blank"
           rel="noopener noreferrer"
           style="
             display: flex;
             align-items: center;
             margin-left: auto;
             padding-right: 12px;
             font-size: 12px;
             font-weight: bold;
             color: var(--jp-ui-font-color1);
             text-decoration: none;
             height: 100%;
           ">
          <svg xmlns="http://www.w3.org/2000/svg"
               width="20"
               height="20"
               viewBox="0 0 39 51"
               style="margin-right: 6px; display: block;">
            <path fill="#F37726" d="M20.005 38.114c-7.85 0-14.706-2.876-18.265-7.134a19.5 19.5 0 0 0 7.069 9.473 19.24 19.24 0 0 0 11.2 3.6c4.013 0 7.927-1.258 11.2-3.6a19.5 19.5 0 0 0 7.069-9.473c-3.567 4.258-10.423 7.134-18.273 7.134m-.002-27.694c7.85 0 14.706 2.876 18.265 7.133a19.5 19.5 0 0 0-7.069-9.473A19.24 19.24 0 0 0 20 4.48a19.24 19.24 0 0 0-11.2 3.6 19.5 19.5 0 0 0-7.069 9.473c3.567-4.248 10.423-7.134 18.273-7.134"></path>
            <path fill="#616161" d="M37.194 3.154a3 3 0 0 1-.426 1.672 2.96 2.96 0 0 1-1.275 1.153 2.93 2.93 0 0 1-3.238-.505 3 3 0 0 1-.776-3.21c.2-.553.558-1.033 1.029-1.38a2.93 2.93 0 0 1 3.733.209c.576.532.919 1.274.953 2.061M9.228 46.393a3.77 3.77 0 0 1-.536 2.11 3.73 3.73 0 0 1-1.608 1.452 3.69 3.69 0 0 1-4.082-.638 3.75 3.75 0 0 1-1.097-1.875 3.8 3.8 0 0 1 .122-2.173 3.74 3.74 0 0 1 1.299-1.739 3.696 3.696 0 0 1 4.704.268 3.76 3.76 0 0 1 1.198 2.595M2.635 9.456a2.17 2.17 0 0 1-1.227-.318 2.2 2.2 0 0 1-.845-.951A2.22 2.22 0 0 1 .935 5.77a2.16 2.16 0 0 1 2.356-.577c.405.15.757.418 1.011.77a2.21 2.21 0 0 1-.156 2.783 2.17 2.17 0 0 1-1.511.71"></path>
          </svg>
          <span>Powered by JupyterLab</span>
        </a>
      `;
      container.id = 'custom-powered-by-label';
      topBar.appendChild(container.node);
      topBarObserver.disconnect();
    });
    topBarObserver.observe(document.body, { childList: true, subtree: true });
  }
};

// Splash

const customSplashPlugin: JupyterFrontEndPlugin<ISplashScreen> = {
  id: 'myorg:custom-splash',
  autoStart: true,
  provides: ISplashScreen,
  activate: () => ({
    show: (light = true) => Private.showSplash(light)
  })
};

namespace Private {
  function createSplash(light: boolean): HTMLElement {
    const splash = document.createElement('div');
    splash.id = 'jp-CustomSplash';
    splash.classList.toggle('light', light);
    splash.classList.toggle('dark', !light);

    const img = document.createElement('img');
    // Just use the inlined data: URI directly:
    img.src = splashGif;
    img.alt = 'Loading…';
    img.style.width = '400px';

    splash.appendChild(img);
    return splash;
  }

  /**
   * Show until JLab calls `.dispose()`. Enforces a 0.8s minimum
   * hold, then fade‑out & removal.
   */
  export function showSplash(light: boolean): IDisposable {
    const element = createSplash(light);
    document.body.appendChild(element);

    const start = Date.now();
    return new DisposableDelegate(() => {
      const elapsed = Date.now() - start;
      const toWait = Math.max(0, 800 - elapsed);

      setTimeout(() => {
        element.classList.add('splash-fade');
        setTimeout(() => {
          element.remove();
        }, 100);
      }, toWait);
    });
  }
}

const plugins: JupyterFrontEndPlugin<any>[] = [
  poweredByPlugin,
  customSplashPlugin
];
export default plugins;