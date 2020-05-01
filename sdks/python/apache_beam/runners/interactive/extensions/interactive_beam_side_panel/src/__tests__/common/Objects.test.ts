import { typedKeys } from '../../common/Objects';

it('lists all keys as strings for the given object', () => {
  class DummyClass {};

  interface IDummyIterface {
    inner_string: string;
    inner_number: number;
  };

  const testObject = {
    a_string: 'a_string',
    b_number: 123,
    c_class: new DummyClass(),
    d_interface: {
      inner_string: 'inner_string',
      inner_number: 456
    } as IDummyIterface
  };

  expect(typedKeys(testObject)).toEqual([
    'a_string',
    'b_number',
    'c_class',
    'd_interface'
  ]);
});
