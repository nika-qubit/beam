import * as React from 'react';

import * as d3 from 'd3';

import { KeyedNumber } from './SourceData';

import { SourceData } from '../common/DataProcessor';

interface D3BarProps {}

interface D3BarState {
  data: object;
}

export class D3Bar extends React.Component<D3BarProps, D3BarState> {
  constructor(props: D3BarProps) {
    super(props);
    this.state = {
      data: {}
    };
  }

  isEmpty() {
    return Object.entries(this.state.data).length === 0;
  }

  updateState(state: D3BarState) {
    this.setState(state, () => this.buildBar());
  }

  buildBar() {
    if (this.isEmpty()) {
      d3.selectAll('#d3Bar')
        .select('g')
        .selectAll('*')
        .remove();
      return;
    }
    const sourceData = this.state.data as SourceData;
    const schema = sourceData.schema.fields;
    const fields = schema
      .filter(field => field.name !== 'index')
      .filter(field => field.type === 'integer')
      .map(field => field.name);
    const data = sourceData.data as Array<KeyedNumber>;

    const stack = d3.stack().keys(fields);

    const stackedSeries = stack(data);

    const g = d3
      .select('#d3Bar')
      .select('g')
      .selectAll('g.series')
      .data(stackedSeries)
      .enter()
      .append('g')
      .classed('series', true)
      .style('fill', '#FBB65B');

    g.selectAll('rect')
      .data(d => {
        return d;
      })
      .enter()
      .append('rect')
      .attr('width', d => {
        return d[1];
      })
      .attr('x', d => {
        return 0;
      })
      .attr('y', (d, i) => {
        return i * 20;
      })
      .attr('height', 19);
  }

  render() {
    return (
      <div>
        <svg id="d3Bar" width="100%" height="100%">
          <g />
        </svg>
      </div>
    );
  }
}
