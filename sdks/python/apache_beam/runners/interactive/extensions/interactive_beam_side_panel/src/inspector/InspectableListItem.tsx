import * as React from 'react';

import {
  ListItem,
  ListItemText,
  ListItemPrimaryText,
  ListItemSecondaryText
} from '@rmwc/list';

import { InspectableViewModel } from './InspectableViewModel';
import { D3Model } from '../d3/D3Model';
import { IInspectableMeta } from './InspectableList';

import '@rmwc/list/styles';

interface IInspectableListItemProps {
  inspectableViewModel?: InspectableViewModel;
  d3Model?: D3Model;
  id: string;
  metadata: IInspectableMeta;
}

interface IInspectableListItemState {}

export class InspectableListItem extends React.Component<
  IInspectableListItemProps,
  IInspectableListItemState
> {
  constructor(props: IInspectableListItemProps) {
    super(props);
    this.show = this.show.bind(this);
  }

  show() {
    this.props.inspectableViewModel.queryKernel(
      this.props.metadata.type,
      this.props.id,
      this.props.inspectableViewModel.options    
    );
    this.props.d3Model.identifier = this.props.id;
  }

  render() {
    return (
      <ListItem
        style={{
          height: '55px',
          paddingLeft: '5px'
        }}
        onClick={this.show}
      >
        <ListItemText>
          <ListItemPrimaryText>{this.props.metadata.name}</ListItemPrimaryText>
          <ListItemSecondaryText>pcollection</ListItemSecondaryText>
        </ListItemText>
      </ListItem>
    );
  }
}
