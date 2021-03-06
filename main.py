#!/usr/bin/env python3
import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests
import tensorflow.contrib.slim as slim


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function [DONE]
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    # load the model
    model = tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)
    graph = tf.get_default_graph()
    image_input = graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob = graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3 = graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4 = graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7 = graph.get_tensor_by_name(vgg_layer7_out_tensor_name)
    
    return image_input, keep_prob, layer3, layer4, layer7


tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer3_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer7_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function [DONE]

    # 1x1 convolution to the last layer of vgg (vgg_layer7_out)
    conv_1x1 = tf.layers.conv2d(vgg_layer7_out, name='conv_1x1', filters=num_classes,
                                kernel_size=1, kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3))

    # upsample to match the size of vgg_layer4_out
    filters1 = vgg_layer4_out.get_shape().as_list()[-1]
    upsample1 = tf.layers.conv2d_transpose(conv_1x1, name='upsample1', filters=filters1,
                                           kernel_size=4, strides=(2, 2), padding='same',
                                           kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3))

    # skip connection: vgg_layer4_out => upsample1
    skip_connection1 = tf.add(upsample1, vgg_layer4_out, name='upsample1')

    # upsample to match the size of vgg_layer3_out
    filters2 = vgg_layer3_out.get_shape().as_list()[-1]
    upsample2 = tf.layers.conv2d_transpose(skip_connection1, name='upsample2', filters=filters2,
                                           kernel_size=4, strides=(2, 2), padding='same',
                                           kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3))

    # skip connection: vgg_layer3_out => upsample2
    skip_connection2 = tf.add(upsample2, vgg_layer3_out, name='skip_connection2')

    # upsample to match the size of the output image
    upsample3 = tf.layers.conv2d_transpose(skip_connection2, name='upsample3', filters=num_classes,
                                           kernel_size=16, strides=(8, 8), padding='same',
                                           kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3))

    return upsample3


tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function [DONE]

    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    correct_label_reshaped = tf.reshape(correct_label, (-1, num_classes))
    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=correct_label_reshaped[:])
    loss_op = tf.reduce_mean(cross_entropy)
    train_op = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(loss_op)
    return logits, train_op, loss_op


tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function [DONE]

    keep_prob_value = 0.75
    learning_rate_value = 0.001
    for epoch in range(epochs):
        total_loss = 0
        for X_batch, gt_batch in get_batches_fn(batch_size):
            loss, _ = sess.run([cross_entropy_loss, train_op],
                               feed_dict={input_image: X_batch, correct_label: gt_batch,
                                          keep_prob: keep_prob_value, learning_rate: learning_rate_value})
            total_loss += loss
        print("EPOCH %d - Loss = %.3f" % (epoch + 1, total_loss))


tests.test_train_nn(train_nn)


def model_summary():
    model_vars = tf.trainable_variables()
    slim.model_analyzer.analyze_vars(model_vars, print_info=True)


def run():
    # adjusting the gpu memory settings
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    config.gpu_options.per_process_gpu_memory_fraction = 0.7

    # configuration
    num_classes = 2
    image_shape = (160, 576)  # KITTI dataset uses 160x576 images
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)
    epochs = 40
    batch_size = 8

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    correct_label = tf.placeholder(tf.float32, name='correct_label')
    learning_rate = tf.placeholder(tf.float32, name='learning_rate')
    with tf.Session(config=config) as sess:
        vgg_path = os.path.join(data_dir, 'vgg')
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # TODO: Build NN using load_vgg, layers, and optimize function [DONE]
        input_image, keep_prob, layer3, layer4, layer7 = load_vgg(sess, vgg_path)
        layer_output = layers(layer3, layer4, layer7, num_classes)

        # print a model summary
        model_summary()

        # TODO: Train NN using the train_nn function [DONE]
        logits, train_op, cross_entropy_loss = optimize(layer_output, correct_label, learning_rate, num_classes)
        sess.run(tf.global_variables_initializer())
        sess.run(tf.local_variables_initializer())

        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image, correct_label, keep_prob, learning_rate)

        # TODO: Save inference data using helper.save_inference_samples [DONE]
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)


if __name__ == '__main__':
    run()
