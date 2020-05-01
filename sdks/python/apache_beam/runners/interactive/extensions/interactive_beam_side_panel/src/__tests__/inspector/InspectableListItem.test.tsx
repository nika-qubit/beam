import * as React from 'react';

import {
  render,
  unmountComponentAtNode
} from 'react-dom';

import { act } from 'react-dom/test-utils';

import { InspectableListItem } from '../../inspector/InspectableListItem';

let container:null | Element = null;
beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
});

afterEach(() => {
  unmountComponentAtNode(container);
  container.remove();
  container = null;
});

it('renders an item', () => {
  act(() => {
    render(
      <InspectableListItem 
        id='id'
        metadata={{
          name: 'name',
          inMemoryId: 123456,
          type: 'pcollection'
        }}  
      />, 
      container);
  });
  const liElement: Element = container.firstElementChild;
  expect(liElement.tagName).toBe('LI');
  expect(liElement.getAttribute('class')).toBe('mdc-list-item');
  const textElement: Element = liElement.firstElementChild;
  expect(textElement.getAttribute('class')).toBe('mdc-list-item__text');
  const primaryTextElement: Element = textElement.firstElementChild;
  expect(primaryTextElement.getAttribute('class')).toBe('mdc-list-item__primary-text');
  expect(primaryTextElement.textContent).toBe('name');
  const secondaryTextElement: Element = textElement.children[1];
  expect(secondaryTextElement.getAttribute('class')).toBe('mdc-list-item__secondary-text');
  expect(secondaryTextElement.textContent).toBe('pcollection');
});
