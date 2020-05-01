import * as React from 'react';

import {
  render,
  unmountComponentAtNode
} from 'react-dom';

import { act } from 'react-dom/test-utils';

import { HtmlView } from '../../common/HtmlView';

import { IHtmlProvider } from '../../common/IHtmlProvider';

let container: null | Element =  null;
beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
});

afterEach(() => {
  unmountComponentAtNode(container);
  container.remove();
  container = null;
});

it('renders provided html', () => {
  const htmlViewRef: React.RefObject<HtmlView> = React.createRef<HtmlView>();
  const spiedConsole = jest.spyOn(console, 'log');
  const fakeHtmlProvider = {
    html: '<div>Test</div>',
    script: [
      'console.log(1);',
      'console.log(2);'
    ]
  } as IHtmlProvider;
  act(() => {
    render(
      <HtmlView
        ref={htmlViewRef}
        htmlProvider={fakeHtmlProvider} />,
      container);
    const htmlView = htmlViewRef.current;
    if (htmlView) {
      htmlView.updateRender();
    }
  });
  const htmlViewElement: Element = container.firstElementChild;
  expect(htmlViewElement.tagName).toBe('DIV');
  expect(htmlViewElement.innerHTML).toBe('<div>Test</div>');
  expect(spiedConsole).toHaveBeenCalledWith(1);
  expect(spiedConsole).toHaveBeenCalledWith(2);
  expect(spiedConsole).toHaveBeenCalledTimes(2);
});

it('only executes incrementally updated Javascript as html provider updated',
  () => {
    const htmlViewRef: React.RefObject<HtmlView> = React.createRef<HtmlView>();
    const spiedConsole = jest.spyOn(console, 'log');
    let fakeHtmlProvider = {
      html: '<div></div>',
      script: ['console.log(1);']
    } as IHtmlProvider;
    act(() => {
      render(
        <HtmlView
          ref={htmlViewRef}
          htmlProvider={fakeHtmlProvider} />,
        container);
      const htmlView = htmlViewRef.current;
      if (htmlView) {
        htmlView.updateRender();
      }
    });
    expect(spiedConsole).toHaveBeenCalledWith(1);
    expect(spiedConsole).toHaveBeenCalledTimes(1);
    fakeHtmlProvider.script.push('console.log(2);');
    act(() => {
      const htmlView = htmlViewRef.current;
      if (htmlView) {
        htmlView.updateRender();
      }
    });
    expect(spiedConsole).toHaveBeenCalledWith(2);
    expect(spiedConsole).toHaveBeenCalledTimes(2);
});
