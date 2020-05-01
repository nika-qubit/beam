import * as React from 'react';

import { IHtmlProvider } from '../common/IHtmlProvider';

interface IHtmlViewProps {
  htmlProvider: IHtmlProvider;
}

interface IHtmlViewState {
  innerHtml: string;
  script: Array<string>;
}

export class HtmlView extends React.Component<IHtmlViewProps, IHtmlViewState> {
  constructor(props: IHtmlViewProps) {
    super(props);
    this.state = {
      innerHtml: props.htmlProvider.html,
      script: []
    };
  }

  componentDidMount() {
    this._updateRenderTimerId = setInterval(() => this.updateRender(), 1000);
  }

  componentWillUnmount() {
    clearInterval(this._updateRenderTimerId);
  }

  updateRender(): void {
    const currentHtml = this.state.innerHtml;
    const htmlToUpdate = this.props.htmlProvider.html;
    const currentScript = this.state.script;
    const scriptToUpdate = [...this.props.htmlProvider.script];
    if (htmlToUpdate !== currentHtml) {
      this.setState({
        innerHtml: htmlToUpdate,
        // As long as html is updated, clear the script state.
        script: []
      });
    }
    /* Depending on whether this iteration updates the html, the scripts
     * are executed differently.
     * Html updated: all scripts are new, start execution from index 0;
     * Html not updated: only newly added scripts need to be executed.
     */
    const currentScriptLength =
      htmlToUpdate === currentHtml ? currentScript.length : 0;
    if (scriptToUpdate.length > currentScriptLength) {
      this.setState(
        {
          script: scriptToUpdate
        },
        // Executes scripts once state is updated.
        () => {
          for (let i = currentScriptLength; i < scriptToUpdate.length; ++i) {
            new Function(scriptToUpdate[i])();
          }
        }
      );
    }
  }

  render() {
    return (
      // This injects raw HTML fetched from kernel into JSX.
      <div dangerouslySetInnerHTML={{ __html: this.state.innerHtml }} />
    );
  }

  private _updateRenderTimerId: number;
}

export function importHtml(hrefs: Array<string>) {
  const webcomponentScript = document.createElement('script');
  webcomponentScript.src =
    'https://cdnjs.cloudflare.com/ajax/libs/webcomponentsjs/1.3.3/webcomponents-lite.js';
  webcomponentScript.type = 'text/javascript';
  webcomponentScript.onload = () => {
    hrefs.forEach(href => {
      const link = document.createElement('link');
      link.rel = 'import';
      link.href = href;
      document.head.appendChild(link);
    });
  };
  document.head.appendChild(webcomponentScript);
}
