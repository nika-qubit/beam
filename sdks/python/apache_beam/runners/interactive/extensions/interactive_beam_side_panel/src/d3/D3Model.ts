import { ISessionContext } from '@jupyterlab/apputils';

import { KernelModel } from '../kernel/KernelModel';

export interface D3Options {
  bubble?: boolean;
  bar?: boolean;
}

// Since interface is not supported by typescript, this concrete object can be
// used to traverse all fields of the interface D3Options.
export const D3_OPTIONS = {
  bubble: false
};

export class D3Model {
  constructor(sessionContext: ISessionContext) {
    this._model = new KernelModel(sessionContext);
  }

  queryKernel(identifier: string) {
    this._identifier = identifier;
    this._model.execute(
      `ie.current_env().inspector.get_pcoll_data('${identifier}')`
    );
  }

  get options(): D3Options {
    return this._options;
  }

  set identifier(identifier: string) {
    if (this._identifier !== identifier) {
      this.queryKernel(identifier);
    }
  }

  set options(options: D3Options) {
    this._options = options;
    this.queryKernel(this._identifier);
  }

  get data(): object {
    return this._model.executeResult;
  }

  private _model: KernelModel;
  private _identifier: string;
  private _options: D3Options = {};
}
