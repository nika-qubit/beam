import { ISessionContext } from '@jupyterlab/apputils';
import { Drawer, DrawerAppContent, DrawerContent } from '@rmwc/drawer';
import {
  TopAppBar,
  TopAppBarFixedAdjust,
  TopAppBarNavigationIcon,
  TopAppBarRow,
  TopAppBarSection,
  TopAppBarTitle
} from '@rmwc/top-app-bar';
import * as React from 'react';

import { Inspectables } from './Inspectables';
import { InspectableView } from './InspectableView';
import { InspectableViewModel } from './InspectableViewModel';
import { D3Model } from '../d3/D3Model';

import '@rmwc/drawer/styles';
import '@rmwc/top-app-bar/styles';

interface IInteractiveInspectorProps {
  sessionContext: ISessionContext;
  inspectableViewModel: InspectableViewModel;
  d3Model: D3Model;
}

interface IInteractiveInspectorState {
  drawerOpen: boolean;
  kernelDisplayName: string;
}

export class InteractiveInspector extends React.Component<
  IInteractiveInspectorProps,
  IInteractiveInspectorState
> {
  constructor(props: IInteractiveInspectorProps) {
    super(props);
    this.state = {
      drawerOpen: true,
      kernelDisplayName: 'no kernel'
    };
    this.flipDrawer = this.flipDrawer.bind(this);
  }

  componentDidMount() {
    this._fetchInitialSessionInfoTimerId = setInterval(
      () => this.fetchInitialSessionInfo(),
      2000
    );
  }

  componentWillUnmount() {
    clearInterval(this._fetchInitialSessionInfoTimerId);
  }

  fetchInitialSessionInfo() {
    if (this.props.sessionContext) {
      const newKernelDisplayName = this.props.sessionContext.kernelDisplayName;
      if (newKernelDisplayName !== this.state.kernelDisplayName) {
        this.setState({
          kernelDisplayName: newKernelDisplayName
        });
      }
    }
  }

  flipDrawer() {
    this.setState({
      drawerOpen: !this.state.drawerOpen
    });
  }

  render() {
    return (
      <React.Fragment>
        <TopAppBar fixed dense>
          <TopAppBarRow>
            <TopAppBarSection>
              <TopAppBarNavigationIcon icon="menu" onClick={this.flipDrawer} />
              <TopAppBarTitle>
                Inspector [kernel:{this.state.kernelDisplayName}]
              </TopAppBarTitle>
            </TopAppBarSection>
          </TopAppBarRow>
        </TopAppBar>
        <TopAppBarFixedAdjust />
        <div className="InteractiveInspector">
          <Drawer dismissible open={this.state.drawerOpen}>
            <DrawerContent>
              <Inspectables
                sessionContext={this.props.sessionContext}
                inspectableViewModel={this.props.inspectableViewModel}
                d3Model={this.props.d3Model}
              />
            </DrawerContent>
          </Drawer>
          <DrawerAppContent>
            <InspectableView
              model={this.props.inspectableViewModel}
              d3Model={this.props.d3Model}
            />
          </DrawerAppContent>
        </div>
      </React.Fragment>
    );
  }

  private _fetchInitialSessionInfoTimerId: number;
}
