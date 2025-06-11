import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  MainAreaWidget,
  IFrame,
  WidgetTracker
} from '@jupyterlab/apputils';

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'experiment-tracker',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    const tracker = new WidgetTracker<MainAreaWidget>({ namespace: 'experiment-tracker' });

    const openTab = async () => {
      let widget = tracker.find(() => true);
      if (widget) {
        app.shell.activateById(widget.id);
        return;
      }

      const iframe = new IFrame();
      iframe.url = '/experiment-tracker/';
      iframe.title.label = 'Experiment Tracker';
      iframe.title.closable = true;
      iframe.id = 'experiment-tracker-frame';
      iframe.sandbox = ['allow-scripts', 'allow-same-origin'];

      widget = new MainAreaWidget({ content: iframe });
      await tracker.add(widget);
      app.shell.add(widget, 'main');
      app.shell.activateById(widget.id);
    };

    const inject = () => {
      const sidebar = document.querySelector('.jp-SideBar.jp-mod-left');
      if (!sidebar) {
        requestAnimationFrame(inject);
        return;
      }

      if (sidebar.querySelector('.experiment-tracker-static-icon')) return;

      const container = document.createElement('div');
      container.className = 'experiment-tracker-static-icon';
      container.title = 'Experiment Tracker';
      container.style.display = 'flex';
      container.style.alignItems = 'center';
      container.style.justifyContent = 'center';
      container.style.height = '52px';
      container.style.cursor = 'pointer';
      container.style.opacity = '0.9';

      const icon = document.createElement('div');
      icon.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#616161"><path d="M200-120q-51 0-72.5-45.5T138-250l222-270v-240h-40q-17 0-28.5-11.5T280-800q0-17 11.5-28.5T320-840h320q17 0 28.5 11.5T680-800q0 17-11.5 28.5T640-760h-40v240l222 270q32 39 10.5 84.5T760-120H200Zm80-120h400L544-400H416L280-240Zm-80 40h560L520-492v-268h-80v268L200-200Zm280-280Z"/></svg>
      `;

      container.appendChild(icon);

      container.addEventListener('click', () => {
        openTab();
      });

      sidebar.insertBefore(container, sidebar.firstChild);
    };

    app.restored.then(() => {
      requestAnimationFrame(inject);
    });
  }
};

export default plugin;