"""
retrieved from https://github.com/princewen/tensorflow_practice/blob/master/RL/Basic-MADDPG-Demo/model_agent_maddpg.py
DDPG model for single agent
Frank Liu,,
"""

import tensorflow as tf

import tensorflow.contrib as tc



class MADDPG:
    # 4,2
    def __init__(self, name, layer_norm=True, nb_actions=3, nb_input = 4, nb_other_aciton = 3):

        gamma = 0.999

        self.layer_norm = layer_norm

        self.nb_actions = nb_actions

        #Placeholders, specified whenever we want to do a forward or backwards pass through the networks

        state_input = tf.placeholder(shape=[None, nb_input], dtype=tf.float32)

        action_input = tf.placeholder(shape=[None, nb_actions], dtype=tf.float32)

        other_action_input = tf.placeholder(shape=[None, nb_other_aciton], dtype=tf.float32)

        reward = tf.placeholder(shape=[None, 1], dtype=tf.float32)



        #This function defines the feed-forward step of the actor. It takes in the state and the actions of other agents, and returns action probabilities

        def actor_network(name):

            with tf.variable_scope(name) as scope:

                x = state_input

                x = tf.layers.dense(x, 64)

                if self.layer_norm:

                    x = tc.layers.layer_norm(x, center=True, scale=True)

                x = tf.nn.relu(x)



                x = tf.layers.dense(x, 64)

                if self.layer_norm:

                    x = tc.layers.layer_norm(x, center=True, scale=True)

                x = tf.nn.relu(x)



                x = tf.layers.dense(x, self.nb_actions,

                                    kernel_initializer=tf.random_uniform_initializer(minval=-3e-3, maxval=3e-3))

                x = tf.nn.softmax(x)

            return x



        #This runs the feed-forward step for the critic network. It takes in the state and actions of the other agents, and returns a value for the state

        def critic_network(name, action_input, reuse=False):

            with tf.variable_scope(name) as scope:

                if reuse:

                    scope.reuse_variables()



                x = state_input

                x = tf.layers.dense(x, 64)

                if self.layer_norm:

                    x = tc.layers.layer_norm(x, center=True, scale=True)

                x = tf.nn.relu(x)



                x = tf.concat([x, action_input], axis=-1)

                x = tf.layers.dense(x, 64)

                if self.layer_norm:

                    x = tc.layers.layer_norm(x, center=True, scale=True)

                x = tf.nn.relu(x)



                x = tf.layers.dense(x, 1, kernel_initializer=tf.random_uniform_initializer(minval=-3e-3, maxval=3e-3))

            return x



        #Calling sess.run on either of these outputs would return the output of the function

        self.action_output = actor_network(name + "_actor")

        self.critic_output = critic_network(name + '_critic',

                                            action_input=tf.concat([action_input, other_action_input], axis=1))

        self.state_input = state_input

        self.action_input = action_input

        self.other_action_input = other_action_input

        self.reward = reward


        #These optimizer objects will handle the back-propagation
        self.actor_optimizer = tf.train.AdamOptimizer(1e-4)

        self.critic_optimizer = tf.train.AdamOptimizer(1e-3)



        # 最大化Q值

        #Negative probability of taking the action that we took. We might need to change this to negative log probability
        self.actor_loss = -tf.reduce_mean(

            critic_network(name + '_critic', action_input=tf.concat([self.action_output, other_action_input], axis=1),

                           reuse=True))

        #Back-propagation step
        self.actor_train = self.actor_optimizer.minimize(self.actor_loss)


        #Target state value - this is the discounted reward
        self.target_Q = tf.placeholder(shape=[None, 1], dtype=tf.float32)

        #Critic loss is mean squared error between the discounted reward and the critic output
        self.critic_loss = tf.reduce_mean(tf.square(self.target_Q - self.critic_output))

        self.critic_train = self.critic_optimizer.minimize(self.critic_loss)

        actor_scope = name + "_actor"
        critic_scope = name + "_critic"
        self.actor_saver = tf.train.Saver(tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=actor_scope), max_to_keep=10)
        self.critic_saver = tf.train.Saver(tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=critic_scope), max_to_keep=10)



    def load_weights(self, name, sess):
        self.actor_saver.restore(sess, name + "_actor")
        self.critic_saver.restore(sess, name + "_critic")

    def save_weights(self, name, sess, episode=None):
        self.actor_saver.save(sess, name + "_actor", global_step=episode)
        self.critic_saver.save(sess, name + "_critic", global_step=episode)


    #This runs the actor_train operation which will perform one train step on the actor network
    def train_actor(self, state, other_action, sess):

        sess.run(self.actor_train, {self.state_input: state, self.other_action_input: other_action})


    #Runs critic_train operation which will perform one train step on critic network
    def train_critic(self, state, action, other_action, target, sess):

        sess.run(self.critic_train,

                 {self.state_input: state, self.action_input: action, self.other_action_input: other_action,

                  self.target_Q: target})


    #Runs action_output which will run a feed-forward step on the actor network
    def action(self, state, sess):

        return sess.run(self.action_output, {self.state_input: state})


    #Runs critic_output which will run a feed-forward on the critic network
    def Q(self, state, action, other_action, sess):

        return sess.run(self.critic_output,

                        {self.state_input: state, self.action_input: action, self.other_action_input: other_action})

