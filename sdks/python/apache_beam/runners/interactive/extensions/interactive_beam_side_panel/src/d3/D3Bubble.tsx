import * as React from 'react';

import * as d3 from 'd3';

import { KeyedNode } from './SourceData';

import { SourceData } from '../common/DataProcessor';

interface D3BubbleProps {}

interface D3BubbleState {
  data: object;
}

export class D3Bubble extends React.Component<D3BubbleProps, D3BubbleState> {
  constructor(props: D3BubbleProps) {
    super(props);
    this.state = {
      data: {}
    };
  }

  componentDidMount() {
    const svg = d3
      .select('#d3Bubble')
      .append('svg')
      .attr('width', '100%')
      .attr('height', '600px');
    const container = svg
      .append('g')
      .attr('width', '100%')
      .attr('height', '600px');
    svg.call(
      d3
        .zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.25, 5])
        .on('zoom', () => {
          container.attr('transform', d3.event.transform);
        })
    );
  }

  isEmpty() {
    return Object.entries(this.state.data).length === 0;
  }

  updateState(state: D3BubbleState) {
    this.setState(state, () => this.buildBubble());
  }

  buildBubble() {
    if (this.isEmpty()) {
      if (this._chart) {
        this._chart.stop();
      }
      d3.selectAll('#d3Bubble')
        .selectAll('svg')
        .selectAll('g')
        .attr('transform', 'none')
        .selectAll('*')
        .remove();
      return;
    }
    const sourceData = this.state.data as SourceData;
    const data = sourceData.data as Array<KeyedNode>;
    let nodes = data.map(d => {
      const radius = d[1] as number;
      const label = d[0] as string;
      return {
        radius: radius / 20,
        label: label,
        ...d
      };
    })
      .sort((x, y) => d3.descending(x.radius, y.radius))
      .slice(0, 1000)  as Array<KeyedNode>;
    nodes = d3.shuffle(nodes, 0, 50);
    const width = parseInt(d3.select('#d3Bubble').style('width'));
    const height = parseInt(d3.select('#d3Bubble').style('height'));
    this._chart = d3
      .forceSimulation(nodes)
      .force('center', d3.forceCenter(width/2, height/2))
      .force('forceX', d3.forceX().strength(0.1).x(width/2))
      .force('forceY', d3.forceY().strength(0.1).y(height/2))
      .force('charge', d3.forceManyBody().strength(-25))
      .force(
        'collision',
        d3.forceCollide().strength(1).radius(d => {
          const datum = d as KeyedNode;
          return datum.radius;
        })
      )
      .on('tick', ticked);
    const u = d3
      .select('#d3Bubble')
      .select('svg')
      .select('g')
      .selectAll<SVGGElement, KeyedNode[]>('g')
      .data(nodes);
    let node = u.enter().append('g');
    node
      .append('circle')
      .attr('r', d => d.radius)
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .style('fill', '#FBB65B')
      .append('svg:title')
      .text(d => d.label);
    node
      .append('text')
      .attr('x', d => d.x)
      .attr('y', d => d.y + d.radius/6)
      .attr('text-anchor', 'middle')
      .style('fill', '#000000')
      .style('font-size', d => d.radius/2)
      .text(d => d.label);
    node.merge(u)
    u.exit().remove();

    function ticked() {
      node.attr('transform', d => {
        return `translate(${d.x}, ${d.y})`;
      });
    }
  }

  render() {
    return <div className="D3View" id="d3Bubble" />;
  }

  private _chart: d3.Simulation<KeyedNode, undefined> | null = null;
}
