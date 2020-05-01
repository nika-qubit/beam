import {
  SessionContext,
  ISessionContext,
  sessionContextDialogs
} from '@jupyterlab/apputils';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import { ServiceManager } from '@jupyterlab/services';

import { Message } from '@lumino/messaging';

import { BoxPanel } from '@lumino/widgets';

import { InteractiveInspectorWidget } from './inspector/InteractiveInspectorWidget';

/**
 * A panel which has the ability to add other children.
 */
export class SidePanel extends BoxPanel {
  constructor(
    manager: ServiceManager.IManager,
    rendermime: IRenderMimeRegistry
  ) {
    super({
      direction: 'top-to-bottom',
      alignment: 'center'
    });
    this.id = 'interactive-beam-inspector';
    this.title.label = 'Interactive Beam Inspector';
    this.title.closable = true;

    this._sessionContext = new SessionContext({
      sessionManager: manager.sessions,
      specsManager: manager.kernelspecs,
      name: 'Interactive Beam Inspector Session'
    });

    this._inspector = new InteractiveInspectorWidget(this._sessionContext);
    this.addWidget(this._inspector);

    void this._sessionContext
      .initialize()
      .then(async value => {
        if (value) {
          const sessionModelItr = manager.sessions.running();
          const firstModel = sessionModelItr.next();
          let onlyOneUniqueKernelExists = true;
          if (firstModel === undefined) {
            // There is zero unique running kernel.
            onlyOneUniqueKernelExists = false;
          } else {
            let sessionModel = sessionModelItr.next();
            while (sessionModel !== undefined) {
              console.log(sessionModel);
              if (sessionModel.kernel.id !== firstModel.kernel.id) {
                // There is more than one unique running kernel.
                onlyOneUniqueKernelExists = false;
                break;
              }
              sessionModel = sessionModelItr.next();
            }
          }
          // Connect to the same session connected to a unique running kernel.
          if (onlyOneUniqueKernelExists) {
            this._sessionContext.sessionManager.connectTo({
              model: firstModel,
              kernelConnectionOptions: {
                handleComms: true
              }
            });
            // Connect to the unique kernel.
            this._sessionContext.changeKernel(firstModel.kernel);
          } else {
            // Let the user choose among sessions and kernels.
            await sessionContextDialogs.selectKernel(this._sessionContext);
          }
        }
      })
      .catch(reason => {
        console.error(
          `Failed to initialize the session in SidePanel.\n${reason}`
        );
      });
  }

  get session(): ISessionContext {
    return this._sessionContext;
  }

  dispose(): void {
    this._sessionContext.dispose();
    super.dispose();
  }

  protected onCloseRequest(msg: Message): void {
    super.onCloseRequest(msg);
    this.dispose();
  }

  private _inspector: InteractiveInspectorWidget;
  private _sessionContext: SessionContext;
}
