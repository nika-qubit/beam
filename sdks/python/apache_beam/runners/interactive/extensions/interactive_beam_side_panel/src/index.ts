import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ICommandPalette } from '@jupyterlab/apputils';

import { ILauncher } from '@jupyterlab/launcher';

import { IMainMenu } from '@jupyterlab/mainmenu';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import { Menu } from '@lumino/widgets';

import { SidePanel } from './SidePanel';

namespace CommandIDs {
  export const open = 'interactive-beam-side-panel:open';
}

/**
 * Initialization data for the interactive_beam_side_panel extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'interactive-beam-side-panel',
  autoStart: true,
  optional: [ILauncher],
  requires: [ICommandPalette, IMainMenu, IRenderMimeRegistry],
  activate: activate
};

function activate(
  app: JupyterFrontEnd,
  palette: ICommandPalette,
  mainMenu: IMainMenu,
  rendermime: IRenderMimeRegistry,
  launcher: ILauncher | null
): void {
  const category = 'Interactive Beam';
  const { commands, shell, serviceManager } = app;

  if (launcher) {
    launcher.add({
      command: CommandIDs.open,
      category: category
    });
  }

  const menu = new Menu({ commands });
  menu.title.label = 'Interactive Beam';
  mainMenu.addMenu(menu);

  async function createPanel(): Promise<SidePanel> {
    const panel = new SidePanel(serviceManager, rendermime);
    shell.add(panel, 'main');
    shell.activateById(panel.id);
    return panel;
  }

  commands.addCommand(CommandIDs.open, {
    label: 'Open Interactive Beam Inspector',
    execute: createPanel
  });

  palette.addItem({ command: CommandIDs.open, category });
  menu.addItem({ command: CommandIDs.open });
}

export default extension;
