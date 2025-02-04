#!/usr/bin/env python

import numpy as np
import random

from q1_softmax import softmax
from q2_gradcheck import gradcheck_naive
from q2_sigmoid import sigmoid, sigmoid_grad

def normalizeRows(x):
    """ Row normalization function
    Implement a function that normalizes each row of a matrix to have
    unit length.
    """

    ### YOUR CODE HERE
    t = np.power(x, 2)
    t = np.sum(t, axis=1)
    t = np.sqrt(t)
    t = t.reshape((x.shape[0], 1))
    x = x / t
    ### END YOUR CODE

    return x

def test_normalize_rows():
    print("Testing normalizeRows...")
    x = normalizeRows(np.array([[3.0,4.0],[1, 2]]))
    print(x)
    ans = np.array([[0.6,0.8],[0.4472136,0.89442719]])
    assert np.allclose(x, ans, rtol=1e-05, atol=1e-06)
    print("")

def softmaxCostAndGradient(predicted, target, outputVectors, dataset):
    """ Softmax cost function for word2vec models
    Implement the cost and gradients for one predicted word vector
    and one target word vector as a building block for word2vec
    models, assuming the softmax prediction function and cross
    entropy loss.
    Arguments:
    predicted -- numpy ndarray, predicted word vector (\hat{v} in
                 the written component)
    target -- integer, the index of the target word
    outputVectors -- "output" vectors (as rows) for all tokens
    dataset -- needed for negative sampling, unused here.
    Return:
    cost -- cross entropy cost for the softmax word prediction
    gradPred -- the gradient with respect to the predicted word
           vector
    grad -- the gradient with respect to all the other word
           vectors
    We will not provide starter code for this function, but feel
    free to reference the code you previously wrote for this
    assignment!
    """

    ### YOUR CODE HERE
    out = np.dot(outputVectors,predicted)
    probs = softmax(out)
    cost = -np.log(probs[target])

    delta3 = probs
    delta3[target] -= 1

    gradPred = np.dot(delta3,outputVectors)
    grad = np.outer(delta3,predicted)
    ### END YOUR CODE

    return cost, gradPred, grad


def  getNegativeSamples(target, dataset, K):
    """ Samples K indexes which are not the target """

    indices = [None] * K
    for k in range(K):
        newidx = dataset.sampleTokenIdx()
        while newidx == target:
            newidx = dataset.sampleTokenIdx()
        indices[k] = newidx
    return indices


def negSamplingCostAndGradient(predicted, target, outputVectors, dataset,
                               K=10):
    """ Negative sampling cost function for word2vec models
    Implement the cost and gradients for one predicted word vector
    and one target word vector as a building block for word2vec
    models, using the negative sampling technique. K is the sample
    size.
    Note: See test_word2vec below for dataset's initialization.
    Arguments/Return Specifications: same as softmaxCostAndGradient
    """

    # Sampling of indices is done for you. Do not modify this if you
    # wish to match the autograder and receive points!
    indices = [target]
    indices.extend(getNegativeSamples(target, dataset, K))

    ### YOUR CODE HERE

    probs = outputVectors.dot(predicted)
    cost = -np.log(sigmoid(probs[target])) - np.sum(np.log(sigmoid(-probs[indices[1:]])))

    opp_sig = (1 - sigmoid(-probs[indices[1:]]))
    gradPred = (sigmoid(probs[target]) - 1) * outputVectors[target] + sum(
        opp_sig[:, np.newaxis] * outputVectors[indices[1:]])

    grad = np.zeros_like(outputVectors)
    grad[target] = (sigmoid(probs[target]) - 1) * predicted

    for k in indices[1:]:
        grad[k] += (1.0 - sigmoid(-np.dot(outputVectors[k], predicted))) * predicted

    ### END YOUR CODE
    return cost, gradPred, grad


def skipgram(currentWord, C, contextWords, tokens, inputVectors, outputVectors,
             dataset, word2vecCostAndGradient=softmaxCostAndGradient):
    """ Skip-gram model in word2vec
    Implement the skip-gram model in this function.
    Arguments:
    currrentWord -- a string of the current center word
    C -- integer, context size
    contextWords -- list of no more than 2*C strings, the context words
    tokens -- a dictionary that maps words to their indices in
              the word vector list
    inputVectors -- "input" word vectors (as rows) for all tokens
    outputVectors -- "output" word vectors (as rows) for all tokens
    word2vecCostAndGradient -- the cost and gradient function for
                               a prediction vector given the target
                               word vectors, could be one of the two
                               cost functions you implemented above.
    Return:
    cost -- the cost function value for the skip-gram model
    grad -- the gradient with respect to the word vectors
    """

    cost = 0.0
    gradIn = np.zeros(inputVectors.shape)
    gradOut = np.zeros(outputVectors.shape)

    ### YOUR CODE HERE

    centerWord_index = tokens[currentWord]
    predicted = inputVectors[centerWord_index]  # centerWord_Vector

    for word in contextWords:
        target = tokens[word]
        loss, gradPred, gradOut_ = word2vecCostAndGradient(predicted, target, outputVectors, dataset)

        gradIn[centerWord_index] += gradPred
        gradOut += gradOut_
        cost += loss
    ### END YOUR CODE

    return cost, gradIn, gradOut


def cbow(currentWord, C, contextWords, tokens, inputVectors, outputVectors,
         dataset, word2vecCostAndGradient=softmaxCostAndGradient):
    """CBOW model in word2vec
    Implement the continuous bag-of-words model in this function.
    Arguments/Return specifications: same as the skip-gram model
    Extra credit: Implementing CBOW is optional, but the gradient
    derivations are not. If you decide not to implement CBOW, remove
    the NotImplementedError.
    """

    cost = 0.0
    gradIn = np.zeros(inputVectors.shape)
    gradOut = np.zeros(outputVectors.shape)

    ### YOUR CODE HERE
    target = tokens[currentWord]
    predicted = np.zeros(inputVectors.shape[1])

    for word in contextWords:
        predicted += inputVectors[tokens[word]]

    cost, gradPred, gradOut = word2vecCostAndGradient(predicted, target, outputVectors, dataset)

    for word in contextWords:
        gradIn[tokens[word]] += gradPred

    ### END YOUR CODE

    return cost, gradIn, gradOut

#############################################
# Testing functions below. DO NOT MODIFY!   #
#############################################

def word2vec_sgd_wrapper(word2vecModel, tokens, wordVectors, dataset, C,
                         word2vecCostAndGradient=softmaxCostAndGradient):
    batchsize = 50
    cost = 0.0
    grad = np.zeros(wordVectors.shape)
    N = wordVectors.shape[0]
    inputVectors = wordVectors[:N/2,:]
    outputVectors = wordVectors[N/2:,:]
    for i in xrange(batchsize):
        C1 = random.randint(1,C)
        centerword, context = dataset.getRandomContext(C1)

        if word2vecModel == skipgram:
            denom = 1
        else:
            denom = 1

        c, gin, gout = word2vecModel(
            centerword, C1, context, tokens, inputVectors, outputVectors,
            dataset, word2vecCostAndGradient)
        cost += c / batchsize / denom
        grad[:N/2, :] += gin / batchsize / denom
        grad[N/2:, :] += gout / batchsize / denom

    return cost, grad


def test_word2vec():
    """ Interface to the dataset for negative sampling """
    dataset = type('dummy', (), {})()
    def dummySampleTokenIdx():
        return random.randint(0, 4)

    def getRandomContext(C):
        tokens = ["a", "b", "c", "d", "e"]
        return tokens[random.randint(0,4)], \
            [tokens[random.randint(0,4)] for i in xrange(2*C)]
    dataset.sampleTokenIdx = dummySampleTokenIdx
    dataset.getRandomContext = getRandomContext

    random.seed(31415)
    np.random.seed(9265)
    dummy_vectors = normalizeRows(np.random.randn(10,3))
    dummy_tokens = dict([("a",0), ("b",1), ("c",2),("d",3),("e",4)])
    print "==== Gradient check for skip-gram ===="
    gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
        skipgram, dummy_tokens, vec, dataset, 5, softmaxCostAndGradient),
        dummy_vectors)
    gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
        skipgram, dummy_tokens, vec, dataset, 5, negSamplingCostAndGradient),
        dummy_vectors)
    print "\n==== Gradient check for CBOW      ===="
    gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
        cbow, dummy_tokens, vec, dataset, 5, softmaxCostAndGradient),
        dummy_vectors)
    gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
        cbow, dummy_tokens, vec, dataset, 5, negSamplingCostAndGradient),
        dummy_vectors)

    print "\n=== Results ==="
    print skipgram("c", 3, ["a", "b", "e", "d", "b", "c"],
        dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset)
    print skipgram("c", 1, ["a", "b"],
        dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset,
        negSamplingCostAndGradient)
    print cbow("a", 2, ["a", "b", "c", "a"],
        dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset)
    print cbow("a", 2, ["a", "b", "a", "c"],
        dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset,
        negSamplingCostAndGradient)


if __name__ == "__main__":
    test_normalize_rows()
    test_word2vec()


# #!/usr/bin/env python
#
# import numpy as np
# import random
#
# from q1_softmax import softmax
# from q2_gradcheck import gradcheck_naive
# from q2_sigmoid import sigmoid, sigmoid_grad
#
# def normalizeRows(x):
#     """ Row normalization function
#
#     Implement a function that normalizes each row of a matrix to have
#     unit length.
#     """
#
#     ### YOUR CODE HERE
#     x = x / np.sqrt(np.sum(x ** 2, keepdims=True, axis=1))
#     ### END YOUR CODE
#
#     return x
#
#
# def test_normalize_rows():
#     print "Testing normalizeRows..."
#     x = normalizeRows(np.array([[3.0,4.0],[1, 2]]))
#     print x
#     ans = np.array([[0.6,0.8],[0.4472136,0.89442719]])
#     assert np.allclose(x, ans, rtol=1e-05, atol=1e-06)
#     print ""
#
#
# def softmaxCostAndGradient(predicted, target, outputVectors, dataset):
#     """ Softmax cost function for word2vec models
#
#     Implement the cost and gradients for one predicted word vector
#     and one target word vector as a building block for word2vec
#     models, assuming the softmax prediction function and cross
#     entropy loss.
#
#     Arguments:
#     predicted -- numpy ndarray, predicted word vector (\hat{v} in
#                  the written component)
#     target -- integer, the index of the target word
#     outputVectors -- "output" vectors (as rows) for all tokens
#     dataset -- needed for negative sampling, unused here.
#
#     Return:
#     cost -- cross entropy cost for the softmax word prediction
#     gradPred -- the gradient with respect to the predicted word
#            vector
#     grad -- the gradient with respect to all the other word
#            vectors
#
#     We will not provide starter code for this function, but feel
#     free to reference the code you previously wrote for this
#     assignment!
#     """
#
#     ### YOUR CODE HERE
#     probs = softmax( predicted.dot(outputVectors.T) )
#     cost = -np.log(probs[target])
#
#     grad_pred = probs
#     grad_pred[target] -= 1
#
#     grad = grad_pred[:, np.newaxis] * predicted[np.newaxis, :]
#     gradPred = grad_pred.dot(outputVectors)
#
#     ### END YOUR CODE
#
#     return cost, gradPred, grad
#
#
# def getNegativeSamples(target, dataset, K):
#     """ Samples K indexes which are not the target """
#
#     indices = [None] * K
#     for k in xrange(K):
#         newidx = dataset.sampleTokenIdx()
#         while newidx == target:
#             newidx = dataset.sampleTokenIdx()
#         indices[k] = newidx
#     return indices
#
#
# def negSamplingCostAndGradient(predicted, target, outputVectors, dataset,
#                                K=10):
#     """ Negative sampling cost function for word2vec models
#
#     Implement the cost and gradients for one predicted word vector
#     and one target word vector as a building block for word2vec
#     models, using the negative sampling technique. K is the sample
#     size.
#
#     Note: See test_word2vec below for dataset's initialization.
#
#     Arguments/Return Specifications: same as softmaxCostAndGradient
#     """
#
#     # Sampling of indices is done for you. Do not modify this if you
#     # wish to match the autograder and receive points!
#     indices = [target]
#     indices.extend(getNegativeSamples(target, dataset, K))
#
#     cost = 0
#     gradPred = 0
#     grad = 0
#     ### YOUR CODE HERE
#     #see p 12 of notes1
#     probs = outputVectors.dot(predicted)
#     cost = -np.log(sigmoid( probs[target] )) - np.sum(np.log(sigmoid( -probs[indices[1:]] )))
#
#     opp_sig = (1 - sigmoid( -probs[indices[1:]] ))
#     gradPred = (sigmoid(probs[target]) - 1) * outputVectors[target] +  sum(opp_sig[:, np.newaxis] * outputVectors[indices[1:]])
#
#     grad = np.zeros_like(outputVectors)
#     grad[target] = (sigmoid(probs[target]) - 1) * predicted
#
#     for k in indices[1:]:
#         grad[k] += (1.0 - sigmoid(-np.dot(outputVectors[k], predicted))) * predicted
#
#     return cost, gradPred, grad
#
#
# def skipgram(currentWord, C, contextWords, tokens, inputVectors, outputVectors,
#              dataset, word2vecCostAndGradient=softmaxCostAndGradient):
#     """ Skip-gram model in word2vec
#
#     Implement the skip-gram model in this function.
#
#     Arguments:
#     currrentWord -- a string of the current center word
#     C -- integer, context size
#     contextWords -- list of no more than 2*C strings, the context words
#     tokens -- a dictionary that maps words to their indices in
#               the word vector list
#     inputVectors -- "input" word vectors (as rows) for all tokens
#     outputVectors -- "output" word vectors (as rows) for all tokens
#     word2vecCostAndGradient -- the cost and gradient function for
#                                a prediction vector given the target
#                                word vectors, could be one of the two
#                                cost functions you implemented above.
#
#     Return:
#     cost -- the cost function value for the skip-gram model
#     grad -- the gradient with respect to the word vectors
#     """
#
#     cost = 0.0
#     gradIn = np.zeros(inputVectors.shape)
#     gradOut = np.zeros(outputVectors.shape)
#
#     ### YOUR CODE HERE
#     center_w = tokens[currentWord] # vector represntation of the center word
#     for context_w in contextWords:
#         # index of target word
#         target = tokens[context_w]
#
#         cost_, gradPred_, gradOut_ = word2vecCostAndGradient(inputVectors[center_w], target, outputVectors, dataset)
#         cost += cost_
#         gradOut += gradOut_
#         gradIn[center_w] += gradPred_
#
#     ### END YOUR CODE
#
#     return cost, gradIn, gradOut
#
#
# def cbow(currentWord, C, contextWords, tokens, inputVectors, outputVectors,
#          dataset, word2vecCostAndGradient=softmaxCostAndGradient):
#     """CBOW model in word2vec
#
#     Implement the continuous bag-of-words model in this function.
#
#     Arguments/Return specifications: same as the skip-gram model
#
#     Extra credit: Implementing CBOW is optional, but the gradient
#     derivations are not. If you decide not to implement CBOW, remove
#     the NotImplementedError.
#     """
#
#     cost = 0.0
#     gradIn = np.zeros(inputVectors.shape)
#     gradOut = np.zeros(outputVectors.shape)
#
#     ### YOUR CODE HERE
#
#     # get integer of the center word (the word we want to predict)
#     target = tokens[currentWord]
#
#     # context_w correspond to the \hat{v} vector
#     context_w = sum(inputVectors[tokens[w]] for w in contextWords)
#
#     cost, gradPred, gradOut = word2vecCostAndGradient(context_w, target, outputVectors, dataset)
#
#     gradIn = np.zeros_like(inputVectors)
#
#     for w in contextWords:
#         gradIn[tokens[w]] += gradPred
#     ### END YOUR CODE
#
#     return cost, gradIn, gradOut
#
#
# #############################################
# # Testing functions below. DO NOT MODIFY!   #
# #############################################
#
# def word2vec_sgd_wrapper(word2vecModel, tokens, wordVectors, dataset, C,
#                          word2vecCostAndGradient=softmaxCostAndGradient):
#     batchsize = 50
#     cost = 0.0
#     grad = np.zeros(wordVectors.shape)
#     N = wordVectors.shape[0]
#     inputVectors = wordVectors[:N/2,:]
#     outputVectors = wordVectors[N/2:,:]
#     for i in xrange(batchsize):
#         C1 = random.randint(1,C)
#         centerword, context = dataset.getRandomContext(C1)
#
#         if word2vecModel == skipgram:
#             denom = 1
#         else:
#             denom = 1
#
#         c, gin, gout = word2vecModel(
#             centerword, C1, context, tokens, inputVectors, outputVectors,
#             dataset, word2vecCostAndGradient)
#         cost += c / batchsize / denom
#         grad[:N/2, :] += gin / batchsize / denom
#         grad[N/2:, :] += gout / batchsize / denom
#
#     return cost, grad
#
#
# def test_word2vec():
#     """ Interface to the dataset for negative sampling """
#     dataset = type('dummy', (), {})()
#     def dummySampleTokenIdx():
#         return random.randint(0, 4)
#
#     def getRandomContext(C):
#         tokens = ["a", "b", "c", "d", "e"]
#         return tokens[random.randint(0,4)], \
#             [tokens[random.randint(0,4)] for i in xrange(2*C)]
#     dataset.sampleTokenIdx = dummySampleTokenIdx
#     dataset.getRandomContext = getRandomContext
#
#     random.seed(31415)
#     np.random.seed(9265)
#     dummy_vectors = normalizeRows(np.random.randn(10,3))
#     dummy_tokens = dict([("a",0), ("b",1), ("c",2),("d",3),("e",4)])
#     print "==== Gradient check for skip-gram ===="
#     gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
#         skipgram, dummy_tokens, vec, dataset, 5, softmaxCostAndGradient),
#         dummy_vectors)
#     gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
#         skipgram, dummy_tokens, vec, dataset, 5, negSamplingCostAndGradient),
#         dummy_vectors)
#     print "\n==== Gradient check for CBOW      ===="
#     gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
#         cbow, dummy_tokens, vec, dataset, 5, softmaxCostAndGradient),
#         dummy_vectors)
#     gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
#         cbow, dummy_tokens, vec, dataset, 5, negSamplingCostAndGradient),
#         dummy_vectors)
#
#     print "\n=== Results ==="
#     print skipgram("c", 3, ["a", "b", "e", "d", "b", "c"],
#         dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset)
#     print skipgram("c", 1, ["a", "b"],
#         dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset,
#         negSamplingCostAndGradient)
#     print cbow("a", 2, ["a", "b", "c", "a"],
#         dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset)
#     print cbow("a", 2, ["a", "b", "a", "c"],
#         dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset,
#         negSamplingCostAndGradient)
#
#
# if __name__ == "__main__":
#     test_normalize_rows()
#     test_word2vec()