import base64
import requests
import io
from PIL import Image
import numpy as np
import json
from loguru import logger


TENSORFLOW_SERVER = "http://localhost:8501/v1/models"


class ModelExecutor:
    @staticmethod
    def execute(model_name, input_data, input_type='text'):
        raise NotImplementedError


class TensorFlowModelExecutor(ModelExecutor):
    @staticmethod
    def pre_process(input_data, spec):
        if 'input-scaling' in spec:
            if 'input-mean' in spec['input-scaling'] and 'input-std' in spect['input-scaling']:
                logger.debug('Perform normalization')
                mean, std = np.array(spec['input-scaling']['input-mean']), np.array(spec['input-scaling']['input-std'])
                return (input_data - mean) / std
            elif 'input-min' in spec['input-scaling'] and 'input-max' in spec['input-scaling']:
                logger.debug('Perform min-max scaling')
                min, max = np.array(spec['input-scaling']['input-min']), np.array(spec['input-scaling']['input-max'])
                return (input_data - min) / (max - min)
        return input_data
    
    def post_process(output, spec):
        ret = output.copy()
        if 'output-mapping' in spec:
            logger.debug('Perform output mapping')
            print(dict(zip(spec['output-mapping'], ret)))
            ret = sorted(zip(spec['output-mapping'], ret), key=lambda x: -x[1])
        if 'output-limit' in spec:
            ret = ret[:spec['output-limit']]
        return ret
    
    @staticmethod
    def execute(model_name, input_data, input_type='text', spec={}):
        server_url = '{host}/{model_name}:predict'.format(host=TENSORFLOW_SERVER, model_name=model_name)

        # image input
        if input_type == 'image':
            input_format = spec['input-format']
            im = Image.open(io.BytesIO(input_data))

            # convert to corresponding mode if needed
            if 'input-image-mode' in spec:
                im = im.convert(spec['input-image-mode'])

            # resize image
            if 'input-image-shape' in spec:
                im = im.resize(spec['input-image-shape'])

            if input_format == 'image_bytes':
                logger.debug('Raw Image Bytes Input')
                img_byte_arr = io.BytesIO()
                im.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                # Compose a JSON Predict request (send JPEG image in base64).
                jpeg_bytes = base64.b64encode(img_byte_arr).decode('utf-8')
                predict_request = '{"instances" : [{"b64": "%s"}]}' % jpeg_bytes
            elif input_format == 'numpy':
                logger.debug('Numpy Input')
                input_arr = np.array(im)
                logger.debug(input_arr.shape)
                input_arr = TensorFlowModelExecutor.pre_process(input_arr, spec)
                # TODO: We must read the signature spec and craft the input correspondingly
                if model_name == 'imagenet_keras_mobilenetv2':
                    predict_request = {"instances": [{"input_image": input_arr.tolist()}]}
                else:
                    predict_request = {"instances": [input_arr.tolist()]}
                predict_request = json.dumps(predict_request)

            # Send request
            response = requests.post(server_url, data=predict_request)
            response.raise_for_status()
            prediction = response.json()['predictions'][0]
            logger.debug(len(prediction))
            if 'classes' in prediction:
                # This is for Resnet with `image_bytes` input
                prediction = prediction['probabilities']
            
            return TensorFlowModelExecutor.post_process(prediction, spec)
        
        elif input_type=='text':
            # text input
            predict_request = '{"inputs" : ["%s"]}' % input_data
            response = requests.post(server_url, data=predict_request)
            response.raise_for_status()
            prediction = response.json()['outputs']['prediction']
            return prediction


class PyTorchModelExecutor(ModelExecutor):
    @staticmethod
    def execute(model_name, input_data, input_type='text'):
        pass
