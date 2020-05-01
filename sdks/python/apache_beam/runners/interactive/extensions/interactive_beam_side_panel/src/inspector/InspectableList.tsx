import * as React from 'react';

import '@rmwc/list/styles';

import { CollapsibleList, SimpleListItem, ListDivider } from '@rmwc/list';

import { InspectableListItem } from './InspectableListItem';

import { InspectableViewModel } from './InspectableViewModel';
import { D3Model } from '../d3/D3Model';

export interface IInspectableMeta {
  name: string;
  inMemoryId: number;
  type: string;
}

interface IKeyedInspectableMeta {
  [key: string]: IInspectableMeta;
}

interface IInspectableListProps {
  inspectableViewModel?: InspectableViewModel;
  d3Model?: D3Model;
  id: string;
  metadata: IInspectableMeta;
  pcolls: IKeyedInspectableMeta;
}

interface IInspectableListState {}

export class InspectableList extends React.Component<
  IInspectableListProps,
  IInspectableListState
> {
  constructor(props: IInspectableListProps) {
    super(props);
  }

  render() {
    const pcollListItems = Object.entries(this.props.pcolls).map(
      ([key, value]) => {
        const propsWithKey = {
          inspectableViewModel: this.props.inspectableViewModel,
          d3Model: this.props.d3Model,
          id: key,
          metadata: value
        };
        return <InspectableListItem key={key} {...propsWithKey} />;
      }
    );
    const onClick = () => {
      this.props.inspectableViewModel.queryKernel(
        this.props.metadata.type,
        this.props.id
      );
    };
    return (
      <React.Fragment>
        <CollapsibleList
          defaultOpen
          handle={
            <SimpleListItem
              style={{
                height: '55px',
                paddingLeft: '0px'
              }}
              text={this.props.metadata.name}
              secondaryText="pipeline"
              metaIcon="chevron_right"
            />
          }
          onOpen={onClick}
          onClose={onClick}
        >
          {pcollListItems}
        </CollapsibleList>
        <ListDivider />
      </React.Fragment>
    );
  }
}
