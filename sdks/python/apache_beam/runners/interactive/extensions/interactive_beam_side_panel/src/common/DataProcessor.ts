export interface SourceData {
  schema: Schema;
  data: Array<KeyedData>;
}

export interface Schema {
  fields: Array<Field>;
  primaryKey: Array<string>;
  [key: string]: any;
}

export interface Field {
  name: string;
  type: string;
}

export interface KeyedData {
  [key: string]: any;
}

export class DataProcessor {

}
