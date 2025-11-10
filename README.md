# Base code from RTWFC

# Real-Time-Writing-With-Fingers

## Introduction

The application allows users to `write on their videos using their fingers in real-time`. It can be used for quick explanations during meetings or maybe online classes. The input feed is taken through the webcam which is parsed through a python script.

Using the `mediapipe` package provided by Google, the user's hand is detected and segmented into 21 landmark points. The coordinates obtained are in turn used to accurately locate,
draw, erase etc depending on the gesture made using the `OpenCV` module available. The user can change the color as well the sizes of the brush and the eraser.

The gestures as follows:

1. `Index finger:` Used to draw on the video.

2. `Index + middle finger:` Used to move around the video and navigate through the navigation bar.

3. `Index + middle + ring + little finger:` Used to erase the written text. 

## Implementation

1. `Processing the video:` This is done through the webcam and it
is accessed using the OpenCV module available in python.
The video must be inverted as the default feed is free of lateral inversion and if we write on this video, the text will be inverted.

2. `Creating the gesture recognition object:` Using the
mediapipe module, we create a class object capable of detecting the user’s hand and return the list of 21 landmark points. By manipulating the coordinates, we can specify the gesture and hence assign functionalities accordingly.

3. `Drawing on the video feed:` Using the coordinates, we can
accurately draw through the OpenCV module. The thickness of
the brush, eraser etc. can be adjusted.

## Challenges faced

1. `Drawing in a smooth and continuous manner:` To draw on the video feed, the simplest method would be to use the cv2.circle() function present in the OpenCV module. However, drawing a circle is a computationally expensive process and hence, doing it in
real time causes the curve to become discontinuous. The solution to this was to store the list of coordinates obtained for every frame and make infintely small line between every subsequent coordinates. This resulted in very small lines joining to form a smooth curve. An analogy would be the method of plotting graphs on coordinate axes.

2. `Drawing on the video feed:` While drawing on another canvas
itself was easy, there was a neat trick involved to
implementing it on the video itself. This can be done by applying the concepts of masking and bitwise operations. Please refer to the source code `drawFeed()` function for better understanding.

## Why not a self-trained model?

One can train their own model instead of using the mediapipe
module available, however, the use of OpenCV would still be involved regardless.

1. The main problem with training one's own model is the `procurement of a dataset large and balanced enough to accurately detect hands.` For the model to properly work accurately without any bias, we need a lot of varieties in the dataset, this is almost impossible to achieve on a personal basis. We also need to tackle the problem of handling noise in the background.

2. Then, arises the problem of `accurately locating the coordinates of the fingertips.` The actions involved require high precision, to draw, erase etc. The reason why the mediapipe module works so well is because Google manually annotated more than 30,000 training images with the landmark points. For training a deep neural network with that many images, we requires huge computational resources, and hence is not feasible.

3. We also need to `keep in mind the latency` as it is real-time in nature. A video generates a lot of frames per second and the model must be capable of handling that.

## Roadmap

The plan ahead would be to make the project more dynamic, I believe it has a lot of potential. Implement a proper GUI for better user experience than what it is capable of providing now. Add more functionalities based on more gestures and make it a proper application capable of running on any user’s system.
