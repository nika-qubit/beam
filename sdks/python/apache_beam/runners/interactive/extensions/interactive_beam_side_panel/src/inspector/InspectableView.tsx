import * as React from 'react';

import {
  InspectableViewModel,
  IOptions,
  IShowOptions
} from './InspectableViewModel';

import { HtmlView } from '../common/HtmlView';

import { IHtmlProvider } from '../common/IHtmlProvider';
import { D3Model, D3Options, D3_OPTIONS } from '../d3/D3Model';
import { typedKeys } from '../common/Objects';

import { D3View } from '../d3/D3View';

import { Checkbox } from '@rmwc/checkbox';

import '@rmwc/checkbox/styles';

type IViewOptions = D3Options;

interface IInspectableViewProps {
  model: InspectableViewModel;
  d3Model: D3Model;
}

interface IInspectableViewState {
  inspectableType: string;
  // options used in kernel messaging.
  options: IOptions;
  // options used in view only.
  viewOptions: IViewOptions;
}

export class InspectableView extends React.Component<
  IInspectableViewProps,
  IInspectableViewState
> {
  constructor(props: IInspectableViewProps) {
    super(props);
    this.state = {
      inspectableType: 'pipeline',
      options: {},
      viewOptions: {}
    };
  }

  componentDidMount() {
    this._updateRenderTimerId = setInterval(() => this.updateRender(), 1500);
  }

  componentWillUnmount() {
    clearInterval(this._updateRenderTimerId);
  }

  updateRender() {
    if (this.props.model.inspectableType === 'pcollection') {
      const showOptions = this.props.model.options as IShowOptions;
      const viewOptions = this.props.d3Model.options as D3Options;
      this.setState({
        inspectableType: 'pcollection',
        options: showOptions,
        viewOptions: viewOptions
      });
    } else {
      this.setState({
        inspectableType: 'pipeline',
        options: {},
        viewOptions: {}
      });
    }
  }

  renderOptions() {
    if (this.props.model.inspectableType === 'pcollection') {
      const showOptions = this.state.options as IShowOptions;
      return (
        <React.Fragment>
          <Checkbox
            label="window info"
            checked={showOptions.includeWindowInfo}
            onChange={e => {
              showOptions.includeWindowInfo = !!e.currentTarget.checked;
              this.props.model.options = showOptions;
            }}
          />
          <Checkbox
            label="facets"
            checked={showOptions.visualizeInFacets}
            onChange={e => {
              showOptions.visualizeInFacets = !!e.currentTarget.checked;
              this.props.model.options = showOptions;
            }}
          />
        </React.Fragment>
      );
    }
    return <span />;
  }

  renderViewOptions() {
    if (this.props.model.inspectableType === 'pcollection') {
      const d3Options = this.state.viewOptions as D3Options;
      const viewOptions = typedKeys(D3_OPTIONS).map(key => {
        return (
          <Checkbox
            key={key}
            label={key}
            checked={d3Options[key]}
            onChange={e => {
              d3Options[key] = !!e.currentTarget.checked;
              this.props.d3Model.options = d3Options;
            }}
          />
        );
      });
      return <React.Fragment>{viewOptions}</React.Fragment>;
    }
  }

  render() {
    const options = this.renderOptions();
    const viewOptions = this.renderViewOptions();
    const htmlProvider = this.props.model as IHtmlProvider;
    return (
      <div className="InspectableView">
        <div>
          {options}
          {viewOptions}
        </div>
        <HtmlView htmlProvider={htmlProvider} />
        <D3View model={this.props.d3Model} />
      </div>
    );
  }

  private _updateRenderTimerId: number;
}
