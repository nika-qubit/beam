import * as React from 'react';

//import * as d3 from 'd3';

interface D3GeoProps {}

interface D3GeoState {
  identifier: string;
  data: object;
}

export class D3Geo extends React.Component<D3GeoProps, D3GeoState> {
  constructor(props: D3GeoProps) {
    super(props);
    this.state = {
      identifier: '',
      data: {}
    };
  }

  updateState(state: D3GeoState) {
    this.setState(state);
    this.buildGeo();
  }

  buildGeo() {}

  geoId() {
    return 'd3geo_' + this.state.identifier;
  }

  render() {
    return (
      <svg id={this.geoId()} width="100%" height="100%">
        <g />
      </svg>
    );
  }
}
