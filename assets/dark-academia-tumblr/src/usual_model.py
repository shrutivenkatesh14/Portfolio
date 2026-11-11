"""
A model made of two parts, built around the blog's usual notes.

Part 1 is a straight line: "a post gets about as many notes as its blog usually gets".
Part 2 is a tree model that learns how much to add or take away because of the post
itself (its words, tags, time and so on). It also sees the usual notes, because the
link between a blog's usual notes and its next post is not a perfect straight line.
Without that, the model scored clearly worse on blogs it had not seen.

Why not use the tree model on its own? A tree model can only predict values it has
seen in its training data. Few blogs in our data get a lot of notes, so a plain tree
model squashed their predictions toward the average. The straight line keeps the
prediction in step with the usual notes, and the trees only work on the leftover part.
"""
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.linear_model import LinearRegression


class UsualNotesModel(BaseEstimator, RegressorMixin):
    """A straight line through the blog's usual notes, with a tree model added on top."""
    def __init__(self, model=None, column="blog_typical_log_notes"):
        self.model = model          # the tree model that works on the leftover part
        self.column = column        # the column that holds the blog's usual notes

    def fit(self, X, y):
        """Learn the line first, then let the tree model learn what is left over."""
        # If the usual-notes column is not there (we leave it out on purpose in one
        # check), there is no line to draw and the tree model does everything.
        self.has_line_ = self.column in X.columns
        if self.has_line_:
            self.line_ = LinearRegression().fit(X[[self.column]], y)
            leftover = y - self.line_.predict(X[[self.column]])
        else:
            leftover = y
        self.model_ = clone(self.model).fit(X, leftover)
        return self

    def predict(self, X):
        """The line's answer plus the tree model's adjustment."""
        part_two = self.model_.predict(X)
        if self.has_line_:
            return self.line_.predict(X[[self.column]]) + part_two
        return np.asarray(part_two)
