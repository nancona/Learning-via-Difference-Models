#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 17:49:02 2017

@author: divyam
"""

import tensorflow as tf
import tflearn
import math



class ActorNetwork(object):
    """
    Input to the network is the state, output is the action
    under a deterministic policy.

    The output layer activation is a tanh to keep the action
    between -2 and 2
    """

    def __init__(self, state_dim, action_dim, action_bound, learning_rate, tau):
        # self.sess = sess
        self.s_dim = state_dim
        self.a_dim = action_dim
        self.action_bound = action_bound
        self.learning_rate = learning_rate
        self.tau = tau

        # Actor Network
        self.inputs, self.out, self.scaled_out = self.create_actor_network()

        self.network_params = tf.trainable_variables()

        # Target Network
        self.target_inputs, self.target_out, self.target_scaled_out = self.create_actor_network()

        self.target_network_params = tf.trainable_variables()[len(self.network_params):]

        # Op for periodically updating target network with online network weights
        self.update_target_network_params = \
            [self.target_network_params[i].assign(tf.multiply(self.network_params[i], self.tau) +
                                                  tf.multiply(self.target_network_params[i], 1. - self.tau))
             for i in range(len(self.target_network_params))]

        # This gradient will be provided by the critic network
        self.action_gradient = tf.placeholder(tf.float32, [None, self.a_dim])

        # Combine the gradients here
        self.actor_gradients = tf.gradients(self.scaled_out, self.network_params, -self.action_gradient)

        # Optimization Op
        self.optimize = tf.train.AdamOptimizer(self.learning_rate). \
            apply_gradients(zip(self.actor_gradients, self.network_params))

        self.num_trainable_vars = len(self.network_params) + len(self.target_network_params)

    def create_actor_network(self):
        inputs = tflearn.input_data(shape=[None, self.s_dim])
        actor_layer1 = tflearn.fully_connected(inputs, 400, activation='relu', name="actorLayer1",
                                               weights_init=tflearn.initializations.uniform(
                                                   minval=-1 / math.sqrt(self.s_dim), maxval=1 / math.sqrt(self.s_dim)))
        actor_layer2 = tflearn.fully_connected(actor_layer1, 300, activation='relu', name="actorLayer2",
                                               weights_init=tflearn.initializations.uniform(minval=-1 / math.sqrt(400),
                                                                                            maxval=1 / math.sqrt(400)))
        # Final layer weights are init to Uniform[-3e-3, 3e-3]
        w_init = tflearn.initializations.uniform(minval=-0.003, maxval=0.003)
        actor_output = tflearn.fully_connected(actor_layer2, self.a_dim, activation='tanh', weights_init=w_init,
                                               name="actorOutput")
        scaled_output = tf.multiply(actor_output, self.action_bound)  # Scale output to -action_bound to action_bound
        return inputs, actor_output, scaled_output

    def train(self, sess, inputs, a_gradient):
        sess.run(self.optimize, feed_dict={
            self.inputs: inputs,
            self.action_gradient: a_gradient
        })

    def predict(self, sess, inputs):
        return sess.run(self.scaled_out, feed_dict={
            self.inputs: inputs
        })

    def predict_target(self, sess, inputs):
        return sess.run(self.target_scaled_out, feed_dict={
            self.target_inputs: inputs
        })

    def update_target_network(self, sess):
        sess.run(self.update_target_network_params)

    def get_num_trainable_vars(self):
        return self.num_trainable_vars
