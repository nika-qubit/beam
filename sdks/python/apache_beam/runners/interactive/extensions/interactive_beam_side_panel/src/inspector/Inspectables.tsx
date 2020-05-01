import { ISessionContext } from '@jupyterlab/apputils';
import { List } from '@rmwc/list';
import * as React from 'react';

import { InspectableList } from './InspectableList';

import { KernelModel } from '../kernel/KernelModel';

import { InspectableViewModel } from './InspectableViewModel';
import { D3Model } from '../d3/D3Model';

import '@rmwc/list/styles';

interface IInspectablesProps {
  sessionContext?: ISessionContext;
  inspectableViewModel?: InspectableViewModel;
  d3Model?: D3Model;
}

interface IInspectablesState {
  inspectables: object;
}

export class Inspectables extends React.Component<
  IInspectablesProps,
  IInspectablesState
> {
  constructor(props: IInspectablesProps) {
    super(props);
    this._inspectKernelCode =
      'from apache_beam.runners.interactive ' +
      'import interactive_environment as ie\n' +
      'ie.current_env().inspector.list_inspectables()';
    this._model = new KernelModel(this.props.sessionContext);
    this.state = { inspectables: this._model.executeResult };
  }

  componentDidMount() {
    this._queryKernelTimerId = setInterval(() => this.queryKernel(), 2000);
    this._updateRenderTimerId = setInterval(() => this.updateRender(), 1000);
  }

  componentWillUnmount() {
    clearInterval(this._queryKernelTimerId);
    clearInterval(this._updateRenderTimerId);
  }

  queryKernel() {
    this._model.execute(this._inspectKernelCode);
  }

  updateRender() {
    const inspectablesToUpdate = this._model.executeResult;
    if (
      Object.keys(inspectablesToUpdate).length &&
      JSON.stringify(this.state.inspectables) !==
        JSON.stringify(inspectablesToUpdate)
    ) {
      this.setState({ inspectables: inspectablesToUpdate });
    }
  }

  render() {
    if (Object.keys(this.state.inspectables).length) {
      const inspectableLists = Object.entries(this.state.inspectables).map(
        ([key, value]) => {
          const propsWithKey = {
            inspectableViewModel: this.props.inspectableViewModel,
            d3Model: this.props.d3Model,
            id: key,
            ...value
          };
          return <InspectableList key={key} {...propsWithKey} />;
        }
      );

      return <List className="Inspectables">{inspectableLists}</List>;
    }

    return <div>No inspectable pipeline nor pcollection has been defined.</div>;
  }

  private _inspectKernelCode: string;
  private _model: KernelModel;
  private _queryKernelTimerId: number;
  private _updateRenderTimerId: number;
}
