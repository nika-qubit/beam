import * as React from 'react';

import { D3Model } from './D3Model';

import { D3Bar } from './D3Bar';
import { D3Bubble } from './D3Bubble';
interface D3ViewProps {
  model: D3Model;
}

interface D3ViewState {
  data: object;
}

export class D3View extends React.Component<D3ViewProps, D3ViewState> {
  constructor(props: D3ViewProps) {
    super(props);
    this.state = {
      data: {}
    };
  }

  componentDidMount() {
    this._updateRenderTimerId = setInterval(() => this.updateRender(), 2000);
  }

  componentWillUnmount() {
    clearInterval(this._updateRenderTimerId);
  }

  updateRender() {
    const dataToUpdate = this.props.model.data;
    const updateNeeded =
      JSON.stringify(this.state.data) !== JSON.stringify(dataToUpdate);
    if (updateNeeded) {
      this.setState({ data: dataToUpdate });
    }

    const barChart = this._barChart.current;
    if (barChart) {
      if (this.props.model.options.bar) {
        if (Object.entries(barChart.state.data).length === 0 || updateNeeded) {
          barChart.updateState({
            data: dataToUpdate
          });
        }
      } else {
        barChart.updateState({
          data: {}
        });
      }
    }

    const bubbleChart = this._bubbleChart.current;
    if (bubbleChart) {
      if (this.props.model.options.bubble) {
        if (bubbleChart.isEmpty() || updateNeeded) {
          bubbleChart.updateState({
            data: dataToUpdate
          });
        }
      } else {
        bubbleChart.updateState({
          data: {}
        });
      }
    }
  }

  render() {
    return (
      <React.Fragment>
        <D3Bubble ref={this._bubbleChart} />
        <D3Bar ref={this._barChart} />
      </React.Fragment>
    );
  }

  private _updateRenderTimerId: number;
  private _barChart: React.RefObject<D3Bar> = React.createRef<D3Bar>();
  private _bubbleChart: React.RefObject<D3Bubble> = React.createRef<D3Bubble>();
}
