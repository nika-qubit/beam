import { ISessionContext } from '@jupyterlab/apputils';

import { IDisplayData, IDisplayUpdate } from '@jupyterlab/nbformat';

import { KernelModel } from '../kernel/KernelModel';

import { IHtmlProvider } from '../common/IHtmlProvider';

export interface IShowOptions {
  includeWindowInfo?: boolean;
  visualizeInFacets?: boolean;
}

export type IOptions = IShowOptions;

export class InspectableViewModel implements IHtmlProvider {
  constructor(sessionContext: ISessionContext) {
    this._model = new KernelModel(sessionContext);
  }

  buildQueryKernelSideRenderingShowGraph() {
    return `ib.show_graph(ie.current_env().inspector.get_val('${
      this._identifier
    }'))`;
  }

  buildQueryKernelSideRenderingShow(options: IShowOptions = {}) {
    let optionsAsString = '';
    if (options.includeWindowInfo) {
      optionsAsString += 'include_window_info=True';
    } else {
      optionsAsString += 'include_window_info=False';
    }
    optionsAsString += ', ';
    if (options.visualizeInFacets) {
      optionsAsString += 'visualize_data=True';
    } else {
      optionsAsString += 'visualize_data=False';
    }
    return (
      'ib.show(' +
      `ie.current_env().inspector.get_val('${this._identifier}'),` +
      optionsAsString +
      ')'
    );
  }

  queryKernel(
    inspectableType: string,
    identifier: string,
    options: IOptions = {}
  ) {
    this._inspectableType = inspectableType.toLowerCase();
    this._identifier = identifier;
    this._options = options;
    if (this._inspectableType === 'pipeline') {
      this._model.execute(this.buildQueryKernelSideRenderingShowGraph());
    } else {
      this._model.execute(
        this.buildQueryKernelSideRenderingShow(options as IShowOptions)
      );
    }
  }

  get inspectableType(): string {
    return this._inspectableType;
  }

  get identifier(): string {
    return this._identifier;
  }

  get options(): IOptions {
    return this._options;
  }

  set options(options: IOptions) {
    this._options = options;
    this.queryKernel(this.inspectableType, this.identifier, this.options);
  }

  get displayData(): Array<IDisplayData> {
    return this._model.displayData;
  }

  get displayUpdate(): Array<IDisplayUpdate> {
    return this._model.displayUpdate;
  }

  get html() {
    return this.displayData
      .map(displayData => this.extractHtmlFromDisplayData(displayData))
      .reduce((accumulatedHtml, html) => accumulatedHtml + html, '');
  }

  get script(): Array<string> {
    return this.displayData.map(displayData =>
      this.extractScriptFromDisplayData(displayData)
    );
  }

  extractHtmlFromDisplayData(displayData: IDisplayData): string {
    let htmlString = '';
    if ('data' in displayData) {
      const data = displayData.data;
      if ('text/html' in data) {
        // Script tag will not execute.
        htmlString += data['text/html'] + '\n';
      }
    }
    return htmlString;
  }

  extractScriptFromDisplayData(displayData: IDisplayData): string {
    let script = '';
    if ('data' in displayData) {
      const data = displayData.data;
      if ('application/javascript' in data) {
        script += data['application/javascript'] + '\n';
      }
      if ('text/html' in data) {
        // Extract script tags from html.
        const div = document.createElement('div');
        div.innerHTML = data['text/html'] as string;
        const scriptTags = div.getElementsByTagName('script');
        for (const el of scriptTags) {
          script += el.text;
        }
      }
    }
    return script;
  }

  private _model: KernelModel;
  private _inspectableType: string;
  private _identifier: string;
  private _options: IOptions = {};
}
