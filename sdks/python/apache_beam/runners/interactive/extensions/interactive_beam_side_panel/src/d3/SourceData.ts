import * as d3 from 'd3';

import {KeyedData} from '../common/DataProcessor';

export interface KeyedNumber extends KeyedData {
  [key: string]: number;
}

export interface KeyedNode extends KeyedData, d3.SimulationNodeDatum {
  radius: number;
  label: string;
  [key: string]: number | string;
}
