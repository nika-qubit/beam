import { ISessionContext, ReactWidget } from '@jupyterlab/apputils';
import * as React from 'react';

import { InteractiveInspector } from './InteractiveInspector';
import { InspectableViewModel } from './InspectableViewModel';
import { importHtml } from '../common/HtmlView';
import { D3Model } from '../d3/D3Model';

export class InteractiveInspectorWidget extends ReactWidget {
  constructor(sessionContext: ISessionContext) {
    super();
    importHtml([
      'https://raw.githubusercontent.com/PAIR-code/facets/1.0.0/facets-dist/facets-jupyter.html'
    ]);
    this._sessionContext = sessionContext;
    // The model is shared by Inspectables and InspectableView so that
    // sub-components of Inspectables can trigger events that alters the
    // InspectableView.
    this._inspectableViewModel = new InspectableViewModel(sessionContext);
    this._d3Model = new D3Model(sessionContext);
  }

  protected render(): React.ReactElement<any> {
    return (
      <InteractiveInspector
        sessionContext={this._sessionContext}
        inspectableViewModel={this._inspectableViewModel}
        d3Model={this._d3Model}
      />
    );
  }

  private _sessionContext: ISessionContext;
  private _inspectableViewModel: InspectableViewModel;
  private _d3Model: D3Model;
}
