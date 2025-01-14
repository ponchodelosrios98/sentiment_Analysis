from collections import Counter
import numpy as np
import time
import sys

# Encapsulate Neural Network in a class
class SentimentNetwork:
    def __init__(self, reviews,labels,min_count = 10, polarity_cutoff = 0.1, hidden_nodes = 10, learning_rate = 0.1):
        """
        Create a SentimenNetwork with the given settings
        Args:
          reviews(list) - List of reviews used for training
          labels(list) - List of POSITIVE/NEGATIVE labels associated with the given reviews
          min_count(int) - Words should only be added to the vocabulary if they occur more than this many times
          polarity_cutoff(float) - The absolute value of a word's positive-to-negative ratio must be at least this big to be considered.
          hidden_nodes(int) - Number of nodes to create in the hidden layer
          learning_rate(float) - Learning rate to use while training
        """
        # Assign a seed to our random number generator to ensure we get
        # reproducable results during development 
        np.random.seed(1)

        # Separates the words and creates counters for Negative / Positive Reviews
        self.pre_process_data(reviews, labels, polarity_cutoff, min_count)
        
        # Build the network to have the number of hidden nodes and the learning rate that
        # were passed into this initializer. Make the same number of input nodes as
        # there are vocabulary words and create a single output node.
        self.init_network(len(self.review_vocab), hidden_nodes, 1, learning_rate)

    def pre_process_data(self, reviews, labels, polarity_cutoff, min_count):
      positive_counts = Counter()
      negative_counts = Counter()
      total_counts = Counter()

      # Split the review in words and add it to label counter
      for i in range(len(reviews)):
        if(labels[i] == 'POSITIVE'):
          for word in reviews[i].split(" "):
            positive_counts[word] += 1
            total_counts[word] += 1
        else:
          for word in reviews[i].split(" "):
            negative_counts[word] += 1
            total_counts[word] += 1

      # Create counter of ratios
      pos_neg_ratios = Counter()

      # Loops over the most common words in both counters
      for term, cnt in list(total_counts.most_common()):
        if (cnt >= 50):
          # If appeared > 50 times, add it to the ratio to detect the repeating in same counters
          pos_neg_ratio = positive_counts[term] / float(negative_counts[term]+1)
          pos_neg_ratios[term] = pos_neg_ratio

      # Applies log to separate the ratios
      for word,ratio in pos_neg_ratios.most_common():
        if (ratio > 1):
          pos_neg_ratios[word] = np.log(ratio)
        else:
          pos_neg_ratios[word] = -np.log((1 / (ratio + 0.01)))

      # Create the vocabulary of total reviews
      review_vocab = set()

      # Iterate over all reviews
      for review in reviews:
        for word in review.split(" "):
          # Just add the word to the vocab if is more than min_count times in the reviews
          if(total_counts[word] > min_count):
            if (word in pos_neg_ratios.keys()):
              # Just adds the word if the ratio is bigger (Positive) or smaller (Negative) than the polarity_cutoff
              if((pos_neg_ratios[word] >= polarity_cutoff) or (pos_neg_ratios[word] <= -polarity_cutoff)):
                review_vocab.add(word)
            else:
              review_vocab.add(word)

      # Convert the vocabulary set to a list so we can access words via indices
      self.review_vocab = list(review_vocab)
      
      # populate label_vocab with all of the words in the given labels.
      label_vocab = set()

      # Positive / Negative Labels
      for label in labels:
        label_vocab.add(label)
      
      # Convert the label vocabulary set to a list so we can access labels via indices
      self.label_vocab = list(label_vocab)
      
      # Store the sizes of the review and label vocabularies.
      self.review_vocab_size = len(self.review_vocab)
      self.label_vocab_size = len(self.label_vocab)
      
      # Create a dictionary of words in the vocabulary mapped to index positions
      self.word2index = {}
      for i, word in enumerate(self.review_vocab):
        self.word2index[word] = i
      
      # Create a dictionary of labels mapped to index positions
      self.label2index = {}
      for i, label in enumerate(self.label_vocab):
        self.label2index[label] = i

    # TODO: All down
    def init_network(self, input_nodes, hidden_nodes, output_nodes, learning_rate):
        # Set number of nodes in input, hidden and output layers.
        self.input_nodes = input_nodes
        self.hidden_nodes = hidden_nodes
        self.output_nodes = output_nodes

        # Store the learning rate
        self.learning_rate = learning_rate

        # Initialize weights

        # These are the weights between the input layer and the hidden layer.
        # Matrix is of the same of input_nodes to hidden_nodes (Layer)
        self.weights_0_1 = np.zeros((self.input_nodes,self.hidden_nodes))

        # These are the weights between the hidden layer and the output layer.
        self.weights_1_2 = np.random.normal(0.0, self.output_nodes**-0.5, 
                                                (self.hidden_nodes, self.output_nodes))
        
        # The input layer, a two-dimensional matrix with shape 1 x hidden_nodes
        # TODO: What does this do?
        self.layer_1 = np.zeros((1,hidden_nodes))
    
    # Returns 0 (Negative) or 1 (Positive)
    def get_target_for_label(self,label):
        if(label == 'POSITIVE'):
            return 1
        else:
            return 0

    # Activation Function    
    def sigmoid(self,x):
        return 1 / (1 + np.exp(-x))
    
    # Derivate Activation Function
    def sigmoid_output_2_derivative(self,output):
        return output * (1 - output)
    
    def train(self, training_reviews_raw, training_labels, epochs):
        # Init training reviews
        training_reviews = list()

        # Loops Over training Reviews
        for review in training_reviews_raw:
            indices = set()
            # Grabs indices of word and put it in the set
            for word in review.split(" "):
                if(word in self.word2index.keys()):
                    indices.add(self.word2index[word])
            training_reviews.append(list(indices))

        # make sure out we have a matching number of reviews and labels
        assert(len(training_reviews) == len(training_labels))
        
        # Keep track of correct predictions to display accuracy during training 
        correct_so_far = 0

        # Remember when we started for printing time statistics
        start = time.time()
        
        # Loop Epoch times
        for epoch in range(epochs):
            # loop through all the given reviews and run a forward and backward pass,
            # updating weights for every item
            for i in range(len(training_reviews)):
                # Get the next review and its correct label
                review = training_reviews[i]
                label = training_labels[i]
                
                # Hidden layer
                self.layer_1 *= 0

                # Layer_1 Grabs the weights of given index
                for index in review:
                    self.layer_1 += self.weights_0_1[index]

                # OActivation Function between weights and inputs
                layer_2 = self.sigmoid(self.layer_1.dot(self.weights_1_2))            
                
                # Output error
                layer_2_error = layer_2 - self.get_target_for_label(label) # Output layer error is the difference between desired target and actual output.
                layer_2_delta = layer_2_error * self.sigmoid_output_2_derivative(layer_2)

                # Backpropagated error
                layer_1_error = layer_2_delta.dot(self.weights_1_2.T) # errors propagated to the hidden layer
                layer_1_delta = layer_1_error # hidden layer gradients - no nonlinearity so it's the same as the error

                # Update the weights
                self.weights_1_2 -= self.layer_1.T.dot(layer_2_delta) * self.learning_rate # update hidden-to-output weights with gradient descent step
                
                for index in review:
                    self.weights_0_1[index] -= layer_1_delta[0] * self.learning_rate # update input-to-hidden weights with gradient descent step

                # Keep track of correct predictions.
                if(layer_2 >= 0.5 and label == 'POSITIVE'):
                    correct_so_far += 1
                elif(layer_2 < 0.5 and label == 'NEGATIVE'):
                    correct_so_far += 1
                
                # For debug purposes, print out our prediction accuracy and speed 
                # throughout the training process. 
                elapsed_time = float(time.time() - start)
                reviews_per_second = i / elapsed_time if elapsed_time > 0 else 0
            print("\rEpoch:" + str(epoch)
                + " #Trained:" + str(((i+1) * (epoch + 1))) \
                + " Training Accuracy:" + str(correct_so_far * 100 / float((i+1) * (epoch + 1)))[:4] + "%")
    
    def test(self, testing_reviews, testing_labels):
        """
        Attempts to predict the labels for the given testing_reviews,
        and uses the test_labels to calculate the accuracy of those predictions.
        """
        # keep track of how many correct predictions we make
        correct = 0
        # we'll time how many predictions per second we make
        start = time.time()

        # Loop through each of the given reviews and call run to predict
        # its label. 
        for i in range(len(testing_reviews)):
            pred = self.run(testing_reviews[i])
            if(pred == testing_labels[i]):
                correct += 1
            
            # For debug purposes, print out our prediction accuracy and speed 
            # throughout the prediction process. 

            elapsed_time = float(time.time() - start)
            reviews_per_second = i / elapsed_time if elapsed_time > 0 else 0
            
            sys.stdout.write("\rProgress:" + str(100 * i/float(len(testing_reviews)))[:4] \
                             + "% Speed(reviews/sec):" + str(reviews_per_second)[0:5] \
                             + " #Correct:" + str(correct) + " #Tested:" + str(i+1) \
                             + " Testing Accuracy:" + str(correct * 100 / float(i+1))[:4] + "%")
    
    def run(self, review):
        """
        Returns a POSITIVE or NEGATIVE prediction for the given review.
        """
        # Run a forward pass through the network, like in the "train" function.
        
        ## New for Project 5: Removed call to update_input_layer function
        #                     because layer_0 is no longer used

        # Hidden layer
        ## New for Project 5: Identify the indices used in the review and then add
        #                     just those weights to layer_1 
        self.layer_1 *= 0
        unique_indices = set()
        for word in review.lower().split(" "):
            if word in self.word2index.keys():
                unique_indices.add(self.word2index[word])
        for index in unique_indices:
            self.layer_1 += self.weights_0_1[index]
        
        # Output layer
        ## New for Project 5: changed to use self.layer_1 instead of local layer_1
        layer_2 = self.sigmoid(self.layer_1.dot(self.weights_1_2))
         
        # Return POSITIVE for values above greater-than-or-equal-to 0.5 in the output layer;
        # return NEGATIVE for other values
        if(layer_2[0] >= 0.5):
            return "POSITIVE"
        else:
            return "NEGATIVE"

# Open Reviews Files and separate them by lines
g = open('reviews.txt','r')
reviews = list(map(lambda x:x[:-1],g.readlines()))
g.close()

# Open Labels (Targets) and separate them by lines
g = open('labels.txt','r')
labels = list(map(lambda x:x[:-1].upper(),g.readlines()))
g.close()

mlp = SentimentNetwork(reviews[:-1000],labels[:-1000],min_count=20,polarity_cutoff=0.05,learning_rate=0.01)
print('--------')
print('TRAINING:')
print('--------')
mlp.train(reviews[:-1000],labels[:-1000], 5)
print('--------')
print('TESTING:')
print('--------')
mlp.test(reviews[-1000:],labels[-1000:])
print('--------')
print('GIVE RANDOM REVIEW')
print('--------')
prediction = mlp.run(reviews[0])
print('{} = {}'.format(prediction, labels[0]))