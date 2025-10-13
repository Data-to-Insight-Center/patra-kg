#!/usr/bin/env python3
"""
Script to send 1000 POST requests to the modelcard endpoint using ImageNet model card payloads.
"""

import requests
import json
import random
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any

# Model card payloads from ImageNet examples
MODEL_CARDS = [
    {
        "name": "resnet18",
        "version": "1.0",
        "short_description": "Image classification using ResNet-18.",
        "full_description": "ResNet-18 is an 18-layer deep convolutional neural network architecture developed by Kaiming He et al. at Microsoft Research. It utilizes residual connections (skip connections) to overcome the vanishing gradient problem, enabling the effective training of deeper networks. ResNet-18 provides a strong balance between performance and computational efficiency for image classification tasks.",
        "keywords": "image classification, deep learning, ResNet, ResNet-18, convolutional neural network, residual connections, image recognition",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-resnet18-1.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "resnet18",
            "version": "1.0",
            "description": "An 18-layer deep convolutional neural network using residual connections for image classification.",
            "owner": "Kaiming He et al.",
            "location": "https://huggingface.co/patra-iu/neelk-resnet18-1.0/blob/main/neelk-resnet18-1.0.pth",
            "license": "BSD-3-Clause",
            "framework": "pytorch",
            "model_type": "convolutional neural network",
            "test_accuracy": 0.70,
            "model_structure": "ResNet-18",
            "metrics": {
                "Precision": 0.70,
                "Recall": 0.70,
                "Backbone": "ResNet-18",
                "Learning_Rate": 0.001,
                "Batch_Size": 64,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    },
    {
        "name": "alexnet",
        "version": "1.0",
        "short_description": "Image classification using the classic AlexNet architecture.",
        "full_description": "AlexNet, introduced in 2012, is a deep convolutional neural network that popularized large-scale image classification benchmarks. It comprises stacked convolution and pooling layers with ReLU activations and dropout for regularization, leading to groundbreaking performance on the ImageNet dataset.",
        "keywords": "image classification, AlexNet, deep learning, convolutional neural network",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "citation": "Krizhevsky, A., Sutskever, I., & Hinton, G. E. (2012). ImageNet classification with deep convolutional neural networks. Advances in Neural Information Processing Systems (NIPS).",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-alexnet-1.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "alexnet",
            "version": "1.0",
            "description": "A deep CNN for large-scale image classification, featuring multiple convolutional and pooling layers, ReLU activations, and dropout.",
            "owner": "Alex Krizhevsky",
            "location": "https://huggingface.co/patra-iu/neelk-alexnet-1.0/blob/main/neelk-alexnet-1.0.pth",
            "license": "Apache License 2.0",
            "framework": "pytorch",
            "model_type": "deep convolutional neural network",
            "test_accuracy": 0.57,
            "model_structure": "AlexNet",
            "metrics": {
                "Precision": 0.56,
                "Recall": 0.55,
                "Number_of_Conv_Layers": 5,
                "Learning_Rate": 0.01,
                "Batch_Size": 128,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    },
    {
        "name": "mobilenet",
        "version": "2.0",
        "short_description": "Image classification using MobileNetV3 Small.",
        "full_description": "MobileNetV3 Small is a lightweight deep convolutional neural network optimized for mobile and edge devices. It combines depthwise separable convolutions with the advancements of MobileNetV2 and introduces novel block structures and squeeze-and-excitation layers to achieve high performance with minimal computational cost.",
        "keywords": "image classification, deep learning, MobileNet, image recognition, lightweight CNN, mobile devices",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "citation": "Howard, A., Sandler, M., Chu, G., Chen, L.-C., Chen, B., Tan, M., Wang, W., Zhu, Y., Pang, R., Adam, H., & Le, Q. V. (2019). Searching for MobileNetV3. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV).",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-mobilenet-2.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "mobilenet",
            "version": "2.0",
            "description": "A lightweight deep convolutional neural network model optimized for mobile and edge devices, using MobileNetV3 architecture with small configurations.",
            "owner": "Google AI",
            "location": "https://huggingface.co/patra-iu/neelk-mobilenet-2.0/blob/main/neelk-mobilenet-2.0.h5",
            "license": "Apache License 2.0",
            "framework": "pytorch",
            "model_type": "lightweight convolutional neural network",
            "test_accuracy": 0.89,
            "model_structure": "MobileNetV3 Small",
            "metrics": {
                "Precision": 0.88,
                "Recall": 0.87,
                "Backbone": "MobileNetV3 Small",
                "Learning_Rate": 0.001,
                "Batch_Size": 128,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    },
    {
        "name": "resnext50",
        "version": "1.0",
        "short_description": "Image classification using ResNeXt-50 32x4d.",
        "full_description": "ResNeXt-50 32x4d is a deep convolutional neural network with a modularized design based on aggregated residual transformations. It achieves high performance on image classification tasks by combining the efficiency of ResNet with additional parallel paths, allowing for more complex representations with fewer parameters.",
        "keywords": "image classification, deep learning, ResNeXt, image recognition, convolutional neural network",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "citation": "Xie, S., Girshick, R., Dollár, P., Tu, Z., & He, K. (2017). Aggregated Residual Transformations for Deep Neural Networks. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR).",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-resnext50-1.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "resnext50",
            "version": "1.0",
            "description": "A deep convolutional neural network model for classifying images, utilizing ResNeXt architecture with 50 layers and a 32x4d configuration.",
            "owner": "Facebook AI Research",
            "location": "https://huggingface.co/patra-iu/neelk-resnext50-1.0/blob/main/neelk-resnext50-1.0.pt",
            "license": "Apache License 2.0",
            "framework": "pytorch",
            "model_type": "convolutional neural network",
            "test_accuracy": 0.94,
            "model_structure": "ResNeXt 50 32x4d",
            "metrics": {
                "Precision": 0.93,
                "Recall": 0.92,
                "Backbone": "ResNeXt-50 32x4d",
                "Learning_Rate": 0.001,
                "Batch_Size": 64,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    },
    {
        "name": "resnet152",
        "version": "1.0",
        "short_description": "Image classification using ResNet-152.",
        "full_description": "ResNet-152 is an 152-layer deep convolutional neural network architecture developed by Kaiming He et al. at Microsoft Research. It utilizes residual connections (skip connections) to overcome the vanishing gradient problem, enabling the effective training of deeper networks. ResNet-152 provides a strong balance between performance and computational efficiency for image classification tasks.",
        "keywords": "image classification, deep learning, ResNet, ResNet-152, convolutional neural network, residual connections, image recognition",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-resnet152-1.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "resnet152",
            "version": "1.0",
            "description": "An 152-layer deep convolutional neural network using residual connections for image classification.",
            "owner": "Kaiming He et al.",
            "location": "https://huggingface.co/patra-iu/neelk-resnet152-1.0/blob/main/neelk-resnet152-1.0.pth",
            "license": "BSD-3-Clause",
            "framework": "pytorch",
            "model_type": "convolutional neural network",
            "test_accuracy": 0.70,
            "model_structure": "ResNet-152",
            "metrics": {
                "Precision": 0.70,
                "Recall": 0.70,
                "Backbone": "ResNet-152",
                "Learning_Rate": 0.001,
                "Batch_Size": 64,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    },
    {
        "name": "shufflenet",
        "version": "1.0",
        "short_description": "Lightweight image classification using ShuffleNet V2 x0.5.",
        "full_description": "ShuffleNet V2 x0.5 is a lightweight and efficient convolutional neural network designed for mobile and embedded devices. It achieves high performance on image classification tasks while maintaining low computational cost through channel split and shuffle operations.",
        "keywords": "image classification, lightweight model, ShuffleNet, image recognition, convolutional neural network",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "citation": "Zhang, X., Zhou, X., Lin, M., & Sun, J. (2018). ShuffleNet: An Extremely Efficient Convolutional Neural Network for Mobile Devices. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR).",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-shufflenet-1.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "shufflenet",
            "version": "1.0",
            "description": "A lightweight convolutional neural network for classifying images, optimized for mobile and embedded applications using ShuffleNet V2 architecture with x0.5 scaling.",
            "owner": "Facebook AI Research",
            "location": "https://huggingface.co/patra-iu/neelk-shufflenet-1.0/blob/main/neelk-shufflenet-1.0.pt",
            "license": "Apache License 2.0",
            "framework": "pytorch",
            "model_type": "convolutional neural network",
            "test_accuracy": 0.89,
            "model_structure": "ShuffleNet V2 x0.5",
            "metrics": {
                "Precision": 0.88,
                "Recall": 0.87,
                "Backbone": "ShuffleNet V2 x0.5",
                "Learning_Rate": 0.005,
                "Batch_Size": 128,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    },
    {
        "name": "densenet201",
        "version": "1.0",
        "short_description": "Image classification using DenseNet201.",
        "full_description": "DenseNet201 is a deep convolutional neural network with densely connected layers, where each layer is connected to every other layer in a feed-forward fashion. This architecture reduces the number of parameters while improving feature reuse and gradient flow, making it highly efficient for image classification tasks.",
        "keywords": "image classification, deep learning, DenseNet, image recognition, convolutional neural network",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "citation": "Huang, G., Liu, Z., Van Der Maaten, L., & Weinberger, K. Q. (2017). Densely connected convolutional networks. In Proceedings of the IEEE conference on computer vision and pattern recognition (pp. 4700-4708). arXiv:1608.06993",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-densenet201-1.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "densenet201",
            "version": "1.0",
            "description": "A deep convolutional neural network model for classifying images, utilizing DenseNet architecture with 201 layers and densely connected blocks.",
            "owner": "Facebook AI Research",
            "location": "https://huggingface.co/patra-iu/neelk-densenet201-1.0/blob/main/neelk-densenet201-1.0.pth",
            "license": "Apache License 2.0",
            "framework": "pytorch",
            "model_type": "convolutional neural network",
            "test_accuracy": 0.93,
            "model_structure": "DenseNet201",
            "metrics": {
                "Precision": 0.92,
                "Recall": 0.91,
                "Backbone": "DenseNet201",
                "Learning_Rate": 0.001,
                "Batch_Size": 64,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    },
    {
        "name": "googlenet",
        "version": "1.0",
        "short_description": "Image classification using GoogLeNet (Inception v1).",
        "full_description": "GoogLeNet, also known as Inception v1, is a 22-layer deep convolutional neural network developed by Google researchers (Christian Szegedy et al.) that won the ImageNet Large Scale Visual Recognition Challenge (ILSVRC) in 2014. It introduced the 'Inception module,' which uses parallel convolutional filters of different sizes within the same block, allowing the network to capture features at multiple scales efficiently. This design significantly reduced the parameter count compared to previous networks while achieving state-of-the-art accuracy.",
        "keywords": "image classification, deep learning, GoogLeNet, Inception, Inception v1, convolutional neural network, ILSVRC 2014",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "citation": "Szegedy, C., Liu, W., Jia, Y., Sermanet, P., Reed, S., Anguelov, D., Erhan, D., Vanhoucke, V., & Rabinovich, A. (2015). Going deeper with convolutions. In Proceedings of the IEEE conference on computer vision and pattern recognition (pp. 1-9). arXiv:1409.4842",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-googlenet-1.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "googlenet",
            "version": "1.0",
            "description": "A deep convolutional neural network (ILSVRC 2014 winner) using Inception modules for image classification.",
            "owner": "Google",
            "location": "https://huggingface.co/patra-iu/neelk-googlenet-1.0/blob/main/neelk-googlenet-1.0.pt",
            "license": "Apache License 2.0",
            "framework": "pytorch",
            "model_type": "convolutional neural network",
            "test_accuracy": 0.70,
            "model_structure": "GoogLeNet / Inception v1",
            "metrics": {
                "Precision": 0.70,
                "Recall": 0.70,
                "Backbone": "GoogLeNet",
                "Learning_Rate": 0.01,
                "Batch_Size": 32,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    },
    {
        "name": "mobilenet",
        "version": "3.0",
        "short_description": "Image classification using MobileNetV3 Small.",
        "full_description": "MobileNetV3 Small is a lightweight deep convolutional neural network optimized for mobile and edge devices. It combines depthwise separable convolutions with the advancements of MobileNetV2 and introduces novel block structures and squeeze-and-excitation layers to achieve high performance with minimal computational cost.",
        "keywords": "image classification, deep learning, MobileNet, image recognition, lightweight CNN, mobile devices",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "citation": "Howard, A., Sandler, M., Chu, G., Chen, L.-C., Chen, B., Tan, M., Wang, W., Zhu, Y., Pang, R., Adam, H., & Le, Q. V. (2019). Searching for MobileNetV3. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV).",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-mobilenet-3.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "MobileNet",
            "version": "3.0",
            "description": "A lightweight deep convolutional neural network model optimized for mobile and edge devices, using MobileNetV3 architecture with small configurations.",
            "owner": "Google AI",
            "location": "https://huggingface.co/patra-iu/neelk-mobilenet-3.0/blob/main/neelk-mobilenet-3.0.h5",
            "license": "Apache License 2.0",
            "framework": "pytorch",
            "model_type": "lightweight convolutional neural network",
            "test_accuracy": 0.89,
            "model_structure": "MobileNetV3 Small",
            "metrics": {
                "Precision": 0.88,
                "Recall": 0.87,
                "Backbone": "MobileNetV3 Small",
                "Learning_Rate": 0.001,
                "Batch_Size": 128,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    },
    {
        "name": "squeezenet",
        "version": "1.0",
        "short_description": "Lightweight CNN for image classification using SqueezeNet 1.0.",
        "full_description": "SqueezeNet 1.0 is a lightweight deep neural network architecture designed for efficient image classification. It achieves competitive accuracy with significantly fewer parameters by using 1×1 filters to reduce the number of input channels to 3×3 filters, combined with downsampling late in the network to maintain spatial resolution.",
        "keywords": "image classification, squeezenet, lightweight CNN",
        "author": "neelk",
        "input_type": "images",
        "category": "classification",
        "citation": "Iandola, F. N., Han, S., Moskewicz, M. W., Ashraf, K., Dally, W. J., & Keutzer, K. (2017). SqueezeNet: AlexNet-level accuracy with 50x fewer parameters and <0.5MB model size. arXiv preprint arXiv:1602.07360.",
        "input_data": "https://www.image-net.org/challenges/LSVRC/2014/index.php",
        "output_data": "https://huggingface.co/patra-iu/neelk-squeezenet-1.0",
        "foundational_model": "None",
        "ai_model": {
            "name": "squeezenet",
            "version": "1.0",
            "description": "A small CNN model for image classification, leveraging the Fire module to reduce the model size while maintaining accuracy.",
            "owner": "DeepScale",
            "location": "https://huggingface.co/patra-iu/neelk-squeezenet-1.0/blob/main/neelk-squeezenet-1.0.pt",
            "license": "Apache License 2.0",
            "framework": "pytorch",
            "model_type": "convolutional neural network",
            "test_accuracy": 0.57,
            "model_structure": "SqueezeNet",
            "metrics": {
                "Precision": 0.56,
                "Recall": 0.55,
                "Backbone": "SqueezeNet",
                "Learning_Rate": 0.005,
                "Batch_Size": 64,
                "Input Shape": "(3, 224, 224)"
            }
        },
        "bias_analysis": {},
        "xai_analysis": {},
        "model_requirements": []
    }
]

# Configuration
ENDPOINT_URL = "http://149.165.175.102:5002/modelcard"
TOTAL_REQUESTS = 1000
MAX_WORKERS = 10  # Number of concurrent threads
REQUEST_TIMEOUT = 30  # Timeout in seconds

# Statistics tracking
stats = {
    'successful': 0,
    'failed': 0,
    'errors': []
}

def send_request(request_id: int) -> Dict[str, Any]:
    """Send a single POST request with a random model card payload."""
    try:
        # Select a random model card
        payload = random.choice(MODEL_CARDS).copy()
        
        # Add a unique identifier to avoid conflicts
        payload['name'] = f"{payload['name']}_{request_id}"
        payload['ai_model']['name'] = f"{payload['ai_model']['name']}_{request_id}"
        
        # Send POST request
        response = requests.post(
            ENDPOINT_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=REQUEST_TIMEOUT
        )
        
        return {
            'request_id': request_id,
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'response_text': response.text[:200] if response.text else '',
            'model_name': payload['name']
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'request_id': request_id,
            'status_code': None,
            'success': False,
            'error': str(e),
            'model_name': payload.get('name', 'unknown') if 'payload' in locals() else 'unknown'
        }
    except Exception as e:
        return {
            'request_id': request_id,
            'status_code': None,
            'success': False,
            'error': f"Unexpected error: {str(e)}",
            'model_name': 'unknown'
        }

def main():
    """Main function to send 1000 POST requests."""
    print(f"Starting to send {TOTAL_REQUESTS} POST requests to {ENDPOINT_URL}")
    print(f"Using {MAX_WORKERS} concurrent workers")
    print(f"Request timeout: {REQUEST_TIMEOUT} seconds")
    print("-" * 60)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all requests
        future_to_id = {
            executor.submit(send_request, i): i 
            for i in range(1, TOTAL_REQUESTS + 1)
        }
        
        # Process completed requests
        for future in as_completed(future_to_id):
            result = future.result()
            
            if result['success']:
                stats['successful'] += 1
                print(f"✓ Request {result['request_id']}: {result['model_name']} - Status {result['status_code']}")
            else:
                stats['failed'] += 1
                error_msg = result.get('error', f"Status {result['status_code']}")
                stats['errors'].append(f"Request {result['request_id']}: {error_msg}")
                print(f"✗ Request {result['request_id']}: {result['model_name']} - {error_msg}")
            
            # Print progress every 50 requests
            total_completed = stats['successful'] + stats['failed']
            if total_completed % 50 == 0:
                print(f"Progress: {total_completed}/{TOTAL_REQUESTS} requests completed")
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Print final statistics
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success rate: {(stats['successful'] / TOTAL_REQUESTS) * 100:.2f}%")
    print(f"Total time: {duration:.2f} seconds")
    print(f"Average time per request: {duration / TOTAL_REQUESTS:.3f} seconds")
    print(f"Requests per second: {TOTAL_REQUESTS / duration:.2f}")
    
    if stats['errors']:
        print(f"\nFirst 10 errors:")
        for error in stats['errors'][:10]:
            print(f"  - {error}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more errors")

if __name__ == "__main__":
    main()
