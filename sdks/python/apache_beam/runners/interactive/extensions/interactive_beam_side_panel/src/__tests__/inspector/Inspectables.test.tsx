import * as React from 'react';

import {
  render,
  unmountComponentAtNode
} from 'react-dom';

import { act } from 'react-dom/test-utils';

import { Inspectables } from '../../inspector/Inspectables';

jest.mock('../../inspector/InspectableList', () => {
  return {
    InspectableList: () => {
      return <div></div>;
    }
  };
});

let container: null | Element = null;
beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
});

afterEach(() => {
  unmountComponentAtNode(container);
  container.remove();
  container = null;
});


it('renders info message about no inspectable when none is available', () => {
  const inspectablesRef: React.RefObject<Inspectables> = React.createRef<Inspectables>();
  act(() => {
    render(
      <Inspectables ref={inspectablesRef} />,
      container);
    const inspectables = inspectablesRef.current;
    if (inspectables) {
      inspectables.setState({inspectables: {}});
    }
  });
  const infoElement: Element = container.firstElementChild;
  expect(infoElement.tagName).toBe('DIV');
  expect(infoElement.textContent).toBe(
    'No inspectable pipeline nor pcollection has been defined.');
});

it('renders inspectables as a list of collapsible lists', () => {
  const inspectablesRef: React.RefObject<Inspectables> = React.createRef<Inspectables>();
  const testData = {
    'pipeline_id1': {
      'metadata': {
        'name': 'pipeline_1',
        'inMemoryId': 1,
        'type': 'pipeline'
      },
      'pcolls': {
        'pcoll_id1': {
          'name': 'pcoll_1', 
          'inMemoryId': 2, 
          'type': 'pcollection'
        }
      }
    },
    'pipeline_id2': {
      'metadata': {
        'name': 'pipeline_2',
        'inMemoryId': 3,
        'type': 'pipeline'
      },
      'pcolls': {
        'pcoll_id2': {
          'name': 'pcoll_2', 
          'inMemoryId': 4, 
          'type': 'pcollection'
        }
      }
    }
  };
  act(() => {
    render(
      <Inspectables ref={inspectablesRef} />,
      container);
    const inspectables = inspectablesRef.current;
    if (inspectables) {
      inspectables.setState({inspectables: testData});
    }
  });
  const listElement: Element = container.firstElementChild;
  expect(listElement.tagName).toBe('UL');
  expect(listElement.getAttribute('class')).toContain('mdc-list');
  // Only checks the length of dummy InspectableList items. Each InspectableList
  // has its own unit tests.
  expect(listElement.children).toHaveLength(2);
});
