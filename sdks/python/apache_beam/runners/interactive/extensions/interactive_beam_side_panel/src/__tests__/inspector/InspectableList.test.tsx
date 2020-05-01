import * as React from 'react';

import {
  render,
  unmountComponentAtNode
} from 'react-dom';

import { act } from 'react-dom/test-utils';

import { InspectableList } from '../../inspector/InspectableList';

import { InspectableViewModel } from '../../inspector/InspectableViewModel';

const mockedInspectableViewModel = new InspectableViewModel({} as any);

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

it('renders a list', () => {
  act(() => {
    render(
      <InspectableList
        inspectableViewModel={mockedInspectableViewModel as any}
        id='pipeline_id'
        metadata={{
          name: 'pipeline_name',
          inMemoryId: 1,
          type: 'pipeline'
        }}
        pcolls={{
          'pcoll_1_id': {
            name: 'pcoll_1_name',
            inMemoryId: 2,
            type: 'pcollection'
          },
          'pcoll_2_id': {
            name: 'pcoll_2_name',
            inMemoryId: 3,
            type: 'pcollection'
          }
        }}
      />,
    container);
  });
  const listElement: Element = container.firstElementChild;
  const listHandle: Element = listElement.firstElementChild;
  expect(listHandle.tagName).toBe('DIV');
  expect(listHandle.getAttribute('class')).toContain('rmwc-collapsible-list__handle');
  const listHandleItem: Element = listHandle.firstElementChild;
  expect(listHandleItem.tagName).toBe('LI');
  expect(listHandleItem.getAttribute('class')).toContain('mdc-list-item');
  const listHandleText: Element = listHandleItem.firstElementChild;
  expect(listHandleText.getAttribute('class')).toContain('mdc-list-item__text');
  const listHandlePrimaryText: Element = listHandleText.firstElementChild;
  expect(listHandlePrimaryText.getAttribute('class')).toContain('mdc-list-item__primary-text');
  expect(listHandlePrimaryText.textContent).toBe('pipeline_name');
  const listHandleMetaIcon: Element = listHandleItem.children[1];
  expect(listHandleMetaIcon.tagName).toBe('I');
  expect(listHandleMetaIcon.getAttribute('class')).toContain('mdc-list-item__meta');
  expect(listHandleMetaIcon.textContent).toBe('chevron_right');
  // Only check existence of collapsible list children because each child is an
  // individual list item that has its own unit tests.
  const listChildren: Element = listElement.children[1];
  expect(listChildren.tagName).toBe('DIV');
  expect(listChildren.getAttribute('class')).toContain('rmwc-collapsible-list__children');
  const listChildItems: HTMLCollection = listChildren.firstElementChild.children;
  expect(listChildItems).toHaveLength(2);
});
