import * as React from 'react';

import { Button } from '@rmwc/button';

import '@rmwc/button/styles';

import {KernelModel} from './KernelModel';

interface IInterruptKernelButtonProps {
  model: KernelModel;
}

interface IInterruptKernelButtonState {
  hidden: boolean;
}

export class InterruptKernelButton extends React.Component<IInterruptKernelButtonProps, IInterruptKernelButtonState> {
  constructor(props: IInterruptKernelButtonProps) {
    super(props);
    this.state = {
      hidden: true
    };
  }

  componentDidMount() {
    this._updateRenderTimerId = setInterval(() => this.updateRender(), 1000);   
  }

  componentWillUnmount() {
    clearInterval(this._updateRenderTimerId);
  }

  updateRender() {
    if (this.props.model.isDone) {
      this.setState({
        hidden: true
      });
    } else {
      this.setState({
        hidden: false
      });
    }
  }

  render() {
    if (this.state.hidden) {
      return (null);
    }
    return (
      <Button
        label='stop' 
        onClick={() => {
          this.props.model.interruptKernel();
          this.setState({
            hidden: true
          });
        }}
        danger
        raised />
    );
  }

  private _updateRenderTimerId: number;
}
