import { KernelModel } from '../../kernel/KernelModel';

const fakeSessionContext = {
  session: {
    kernel: {
      requestExecute: () => {
        return {
          onIOPub: () => {}
        };
      }
    }
  }
};

it('creates new future with IOPub callbacks when executing new code in kernel',
  () => {
  const kernelModel = new KernelModel(fakeSessionContext as any);
  kernelModel.execute('new code');
  expect(kernelModel.future).not.toBe(null);
  expect(kernelModel.future.onIOPub).not.toBe(null);
});

it('handles execute result from IOPub channel', () => {
  const kernelModel = new KernelModel(fakeSessionContext as any);
  kernelModel.execute('any code');
  kernelModel.future.onIOPub({
    header: {
      msg_type: 'execute_result'
    },
    content: {
      data: {
        'text/plain': '\'{"pipeline_id": {"metadata": {"name": "pipeline", "inMemoryId": 1, "type": "pipeline"}, "pcolls": {"pcoll_id": {"name": "pcoll", "inMemoryId": 2, "type": "pcollection"}}}}\''
      },
      channel: 'iopub'
    }
  } as any);
  expect(kernelModel.executeResult).toEqual({
    'pipeline_id': {
      'metadata': {
        'name': 'pipeline',
        'inMemoryId': 1,
        'type': 'pipeline'
      },
      'pcolls': {
        'pcoll_id': {
          'name': 'pcoll',
          'inMemoryId': 2,
          'type': 'pcollection'
        }
      }
    }
  });
});

it('handles display data from IOPub channel', () => {
  const kernelModel = new KernelModel(fakeSessionContext as any);
  kernelModel.execute('any code');
  const displayData = {
    output_type: 'display_data',
    data: {
      'text/html': '<div></div>',
      'application/javascript': 'console.log(1);'
    },
    metadata: {
      'some': 'data'
    }
  };

  kernelModel.future.onIOPub({
    header: {
      msg_type: 'display_data'
    },
    content: displayData
  } as any);
  expect(kernelModel.displayData).toEqual([displayData]);
});

it('handles display update from IOPub channel', () => {
  const kernelModel = new KernelModel(fakeSessionContext as any);
  kernelModel.execute('any code');
  const updateDisplayData = {
    output_type: 'update_display_data',
    data: {
      'text/html': '<div id="abc"></div>',
      'application/javascript': 'console.log(2)'
    },
    metadata: {
      'some': 'data'
    }
  };
  kernelModel.future.onIOPub({
    header: {
      msg_type: 'update_display_data'
    },
    content: updateDisplayData
  } as any);
  expect(kernelModel.displayUpdate).toEqual([updateDisplayData]);
});
