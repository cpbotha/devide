# highly optimized tkinter tree control
# by Charles E. "Gene" Cash <gcash@cfl.rr.com>
#
# thanks to Laurent Claustre <claustre@esrf.fr> for sending lots of helpful
# bug reports.
#
# This copyright license is intended to be similar to the FreeBSD license. 
#
# Copyright 1998 Gene Cash All rights reserved. 
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the
#       distribution.
#
# THIS SOFTWARE IS PROVIDED BY GENE CASH ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# This means you may do anything you want with this code, except claim you
# wrote it. Also, if it breaks you get to keep both pieces.
#
# 02-DEC-98 started
# 22-NOV-99 Changed garbage collection to a better algorithm.
# 28-AUG-01 added logic to deal with exceptions in user callbacks
# 02-SEP-01 fixed hang when closing last node
# 07-SEP-01 added binding tracking so nodes got garbage-collected
#           also fixed subclass call to initialize Canvas to properly deal
#           with variable arguments and keyword arguments
# 11-SEP-01 bugfix for unbinding code
# 13-OCT-01 added delete & insert methods for nodes (by email request)
#           LOTS of code cleanup
#           changed leading double underscores to PVT nomenclature
#           added ability to pass Node subclass to Tree constructor
#           removed after_callback since subclassing Node is better idea
# 15-OCT-01 finally added drag'n'drop support.  it consisted of a simple
#           change to the Node PVT_click method, and addition of logic like
#           the example in Tkdnd.py.  It took 3 days to grok the Tkdnd example
#           and 2 hours to make the code changes.  Plus another 1/2 day to get
#           a working where() function.
# 16-OCT-01 incorporated fixes to delete() and dnd_commit() bugs by
#           Laurent Claustre <claustre@esrf.fr>
# 17-OCT-01 added find_full_id() and cursor_node() methods
# 18-OCT-01 fixes to delete() on root during collapse and with
#           drag-in-progress flag by Laurent Claustre <claustre@esrf.fr>
# 10-FEB-02 fix to prev_visible() by Nicolas Pascal <pascal@esrf.fr>
#           fixes which made insert_before()/insert_after() actually work.
#           also added expand/collapse indicators like Internet Explorer
#           as requested by Nicolas.
# 11-FEB-02 another fix to prev_visible().  it works this time.  honest.

import Tkdnd
from Tkinter import *

#------------------------------------------------------------------------------
def report_callback_exception():
    """report exception on sys.stderr."""
    import traceback
    import sys
    
    sys.stderr.write("Exception in Tree control callback\n")
    traceback.print_exc()
    
#------------------------------------------------------------------------------
# add_node() helper object
class Struct:
    """Helper object for add_node() method"""
    def __init__(self):
        pass

#------------------------------------------------------------------------------
# tree node helper class
class Node:
    # initialization creates node, draws it, and binds mouseclicks
    def __init__(self, parent_node, id, collapsed_icon, x, y,
                 parent_widget=None, expanded_icon=None, label=None,
                 expandable_flag=0):
        # immediate parent node
        self.parent_node=parent_node
        # internal name used to manipulate things
        self.id=id
        # bitmaps to be displayed
        self.expanded_icon=expanded_icon
        self.collapsed_icon=collapsed_icon
        # tree widget we belong to
        if parent_widget:
            self.widget=parent_widget
        else:
            self.widget=parent_node.widget
        # for speed
        sw=self.widget
        # our list of child nodes
        self.child_nodes=[]
        # flag that node can be expanded
        self.expandable_flag=expandable_flag
        self.expanded_flag=0
        # add line
        if parent_node and sw.line_flag:
            self.h_line=sw.create_line(x, y, x-sw.dist_x, y)
        else:
            self.h_line=None
        self.v_line=None
        # draw approprate image
        self.symbol=sw.create_image(x, y, image=self.collapsed_icon)
        # add expand/collapse indicator
        self.indic=None
        if expandable_flag and sw.line_flag and sw.plus_icon and sw.minus_icon:
            self.indic=sw.create_image(x-sw.dist_x, y, image=sw.plus_icon)
        # add label
        self.label=sw.create_text(x+sw.text_offset, y, text=label, anchor='w')
        # single-click to expand/collapse
        if self.indic:
            sw.tag_bind(self.indic, '<1>', self.PVT_click)
        else:
            sw.tag_bind(self.symbol, '<1>', self.PVT_click)
        # for drag'n'drop target detection
        sw.tag_bind(self.symbol, '<Any-Enter>', self.PVT_enter)
        sw.tag_bind(self.label, '<Any-Enter>', self.PVT_enter)

    # for testing (gotta make sure nodes get properly GC'ed)
    #def __del__(self):
    #    print self.full_id(), 'deleted'

    # ----- PUBLIC METHODS -----
    def set_collapsed_icon(self, icon):
        self.collapsed_icon=icon
        if not self.expanded_flag:
            self.widget.itemconfig(self.symbol, image=icon)

    def set_expanded_icon(self, icon):
        self.expanded_icon=icon
        if self.expanded_flag:
            self.widget.itemconfig(self.symbol, image=icon)

    def parent(self):
        return self.parent_node

    def prev_sib(self):
        i=self.parent_node.child_nodes.index(self)-1
        if i >= 0:
            return self.parent_node.child_nodes[i]
        else:
            return None

    def next_sib(self):
        i=self.parent_node.child_nodes.index(self)+1
        if i < len(self.parent_node.child_nodes):
            return self.parent_node.child_nodes[i]
        else:
            return None
        
    # return next lower visible node
    def next_visible(self):
        n=self
        if n.child_nodes:
            # if you can go right, do so
            return n.child_nodes[0]
        while n.parent_node:
            # move to next sibling
            i=n.parent_node.child_nodes.index(n)+1
            if i < len(n.parent_node.child_nodes):
                return n.parent_node.child_nodes[i]
            # if no siblings, move to parent's sibling
            n=n.parent_node
        # we're at bottom
        return self
    
    # return next higher visible node
    def prev_visible(self):
        n=self
        if n.parent_node:
            i=n.parent_node.child_nodes.index(n)-1
            if i < 0:
                return n.parent_node
            else:
                j=n.parent_node.child_nodes[i]
                return j.PVT_last()
        else:
            return n
                
    def children(self):
        return self.child_nodes

    def get_label(self):
        return self.widget.itemcget(self.label, 'text')

    def set_label(self, label):
        self.widget.itemconfig(self.label, text=label)

    # returns true if expanded, false otherwise
    def expanded(self):
        return self.expanded_flag

    # returns true if node can be expanded
    def expandable(self):
        return self.expandable_flag
    
    # get name & names of all parents as a list
    def full_id(self):
        if self.parent_node:
            return self.parent_node.full_id()+(self.id,)
        else:
            return (self.id,)

    def expand(self):
        if not self.expanded_flag:
            self.PVT_set_state(1)
        
    def collapse(self):
        if self.expanded_flag:
            self.PVT_set_state(0)

    # delete node from tree
    # ("me_too" is a hack not to be used by external code, please)
    def delete(self, me_too=1):
        sw=self.widget
        if not self.parent_node and me_too:
            # can't delete the root node
            raise ValueError, "can't delete root node"
        self.PVT_delete_subtree()
        # move everything up so that distance to next subnode is correct
        n=self.next_visible()
        x1, y1=sw.coords(self.symbol)
        x2, y2=sw.coords(n.symbol)
        if me_too:
            dist=y2-y1
        else:
            dist=y2-y1-sw.dist_y
        self.PVT_tag_move(-dist)
        n=self
        if me_too:
            if sw.pos == self:
                # move cursor if it points to current node
                sw.move_cursor(self.parent_node)
            self.PVT_unbind_all()
            sw.delete(self.symbol)
            sw.delete(self.label)
            sw.delete(self.h_line)
            sw.delete(self.v_line)
            sw.delete(self.indic)
            self.parent_node.child_nodes.remove(self)
            # break circular ref now, so parent may be GC'ed later
            n=self.parent_node
            self.parent_node=None
        n.PVT_cleanup_lines()
        n.PVT_update_scrollregion()

    # call parent tree's add_node() function to generate the list of nodes
    def insert_before(self, nodes):
        i=self.parent_node.child_nodes.index(self)
        self.parent_node.PVT_insert(nodes, i, self.prev_visible())
    
    def insert_after(self, nodes):
        i=self.parent_node.child_nodes.index(self)+1
        self.parent_node.PVT_insert(nodes, i, self.PVT_last())
        
    def insert_children(self, nodes):
        self.PVT_insert(nodes, 0, self)
        
    def toggle_state(self):
        if self.expandable_flag:
            if self.expanded_flag:
                self.PVT_set_state(0)
            else:
                self.PVT_set_state(1)
                
    # ----- functions for drag'n'drop support -----
    # detect mouse hover after drop
    def PVT_enter(self, event):
        self.widget.target=self
        
    # poke us with a fork, we're done
    # this means dnd processing has been ended, it DOES NOT imply that
    # we've been dropped somewhere useful, we could have just been dropped
    # into deep space and nothing happened to any data structures, or it
    # could have been just a plain mouse-click w/o any dragging  
    def dnd_end(self, target, event):
        if not self.widget.drag:
            # if there's been no dragging, it was just a mouse click
            self.widget.move_cursor(self)
            self.toggle_state()
        self.widget.drag=0

    # ----- PRIVATE METHODS (prefixed with "PVT_") -----
    # these methods are subject to change, so please try not to use them
    #
    # return bottom-most node in subtree
    def PVT_last(self):
        n=self
        while n.child_nodes:
            n=n.child_nodes[-1]
        return n
    
    # search for a particular node
    def PVT_find(self, search):
        if self.id != search[0]:
            # this actually only goes tilt if root doesn't match
            return None
        if len(search) == 1:
            return self
        # get list of children IDs
        i=map(lambda x: x.id, self.child_nodes)
        # if there is a child that matches, search it
        try:
            return self.child_nodes[i.index(search[1])].PVT_find(search[1:])
        except:
            return None

    # create and insert new children
    # "nodes" is list previously created via calls to add_list()
    # "pos" is index in the list of children where the new nodes are inserted
    # "below" is node which new children should appear immediately below
    def PVT_insert(self, nodes, pos, below):
        if not self.expandable_flag:
            raise TypeError, 'not an expandable node'
        # for speed
        sw=self.widget
        # expand and insert children
        children=[]
        self.expanded_flag=1
        sw.itemconfig(self.symbol, image=self.expanded_icon)
        if sw.minus_icon:
            sw.itemconfig(self.indic, image=sw.minus_icon)
        if len(nodes):
            # move stuff to make room
            below.PVT_tag_move(sw.dist_y*len(nodes))
            # get position of first new child
            xp, dummy=sw.coords(self.symbol)
            dummy, yp=sw.coords(below.symbol)
            xp=xp+sw.dist_x
            yp=yp+sw.dist_y
            # create vertical line
            if sw.line_flag and not self.v_line:
                self.v_line=sw.create_line(
                    xp, yp,
                    xp, yp+sw.dist_y*len(nodes))
                sw.tag_lower(self.v_line, self.symbol)
            n=sw.node_class
            for i in nodes:
                # add new subnodes, they'll draw themselves
                # this is a very expensive call
                children.append(
                    n(parent_node=self, expandable_flag=i.flag, label=i.name,
                      id=i.id, collapsed_icon=i.collapsed_icon,
                      expanded_icon=i.expanded_icon, x=xp, y=yp))
                yp=yp+sw.dist_y
            self.child_nodes[pos:pos]=children
            self.PVT_cleanup_lines()
            self.PVT_update_scrollregion()
            sw.move_cursor(sw.pos)
        
    # expanding/collapsing folders
    def PVT_set_state(self, state):
        # not re-entrant, and there are certain cases in which we can be
        # called again before we're done
        # acquire mutex
        while self.widget.spinlock:
            pass
        self.widget.spinlock=1
        # expand & draw our subtrees
        if state:
            self.child_nodes=[]
            self.widget.new_nodes=[]
            if self.widget.get_contents_callback:
                # this callback needs to make multiple calls to add_node()
                try:
                    self.widget.get_contents_callback(self)
                except:
                    report_callback_exception()
            self.PVT_insert(self.widget.new_nodes, 0, self)
        # collapse and delete subtrees
        else:
            self.expanded_flag=0
            self.widget.itemconfig(self.symbol, image=self.collapsed_icon)
            if self.indic:
                self.widget.itemconfig(self.indic, image=self.widget.plus_icon)
            self.delete(0)
        # release mutex
        self.widget.spinlock=0

    # resize connecting lines
    def PVT_cleanup_lines(self):
        if self.widget.line_flag:
            n=self
            while n:
                if n.child_nodes:
                    x1, y1=self.widget.coords(n.symbol)
                    x2, y2=self.widget.coords(n.child_nodes[-1].symbol)
                    self.widget.coords(n.v_line, x1, y1, x1, y2)
                n=n.parent_node

    # update scroll region for new size
    def PVT_update_scrollregion(self):
        x1, y1, x2, y2=self.widget.bbox('all')
        self.widget.configure(scrollregion=(x1, y1, x2+5, y2+5))

    # recursively delete subtree & clean up cyclic references
    def PVT_delete_subtree(self):
        sw=self.widget
        sw.delete(self.v_line)
        self.v_line=None
        for i in self.child_nodes:
            # delete node's subtree, if any
            i.PVT_delete_subtree()
            i.PVT_unbind_all()
            # delete widgets from canvas
            sw.delete(i.symbol)
            sw.delete(i.label)
            sw.delete(i.h_line)
            sw.delete(i.v_line)
            sw.delete(i.indic)
            # break circular reference
            i.parent_node=None
        # move cursor if it's in deleted subtree
        if sw.pos in self.child_nodes:
            sw.move_cursor(self)
        # now subnodes will be properly garbage collected
        self.child_nodes=[]
        
    # unbind callbacks so node gets garbage-collected
    # this wasn't easy to figure out the proper way to do this
    def PVT_unbind_all(self):
        for j in (self.symbol, self.label, self.indic, self.h_line,
                  self.v_line):
            for k in self.widget.bindings.get(j, ()):
                self.widget.tag_unbind(j, k[0], k[1])

    # move everything below current icon, to make room for subtree
    # using the Disney magic of item tags
    def PVT_tag_move(self, dist):
        # mark everything below current node as movable
        bbox1=self.widget.bbox(self.widget.root.symbol, self.label)
        bbox2=self.widget.bbox('all')
        self.widget.dtag('move')
        self.widget.addtag('move', 'overlapping', 
                           bbox2[0], bbox1[3], bbox2[2], bbox2[3])
        # untag cursor & node so they don't get moved too
        self.widget.dtag(self.widget.cursor_box, 'move')
        self.widget.dtag(self.symbol, 'move')
        self.widget.dtag(self.label, 'move')
        # now do the move of all the tagged objects
        self.widget.move('move', 0, dist)
    
    # handle mouse clicks by kicking off possible drag'n'drop processing
    def PVT_click(self, event):
        if self.widget.drop_callback:
            if Tkdnd.dnd_start(self, event):
                x1, y1, x2, y2=self.widget.bbox(self.symbol)
                self.x_off=(x1-x2)/2
                self.y_off=(y1-y2)/2
        else:
            # no callback, don't bother with drag'n'drop
            self.widget.drag=0
            self.dnd_end(None, None)

#------------------------------------------------------------------------------
class Tree(Canvas):
    # do we have enough possible arguments?!?!?!
    def __init__(self, master, root_id, root_label='',
                 get_contents_callback=None, dist_x=15, dist_y=15,
                 text_offset=10, line_flag=1, expanded_icon=None,
                 collapsed_icon=None, regular_icon=None, plus_icon=None,
                 minus_icon=None, node_class=Node, drop_callback=None,
                 *args, **kw_args):
        # pass args to superclass
        # this is the ONLY proper way to handle variable arguments and
        # variable keyword arguments
        apply(Canvas.__init__, (self, master)+args, kw_args)
        # this allows to subclass Node and pass our class in
        self.node_class=node_class
        # keep track of node bindings
        self.bindings={}
        # cheap mutex spinlock
        self.spinlock=0
        # flag to see if there's been any d&d dragging
        self.drag=0
        # default images (BASE64-encoded GIF files)
        if expanded_icon == None:
            self.expanded_icon=PhotoImage(
                data='R0lGODlhEAANAKIAAAAAAMDAwICAgP//////ADAwMAAAAAAA' \
                'ACH5BAEAAAEALAAAAAAQAA0AAAM6GCrM+jCIQamIbw6ybXNSx3GVB' \
                'YRiygnA534Eq5UlO8jUqLYsquuy0+SXap1CxBHr+HoBjoGndDpNAAA7')
        else:
            self.expanded_icon=expanded_icon
        if collapsed_icon == None:
            self.collapsed_icon=PhotoImage(
                data='R0lGODlhDwANAKIAAAAAAMDAwICAgP//////ADAwMAAAAAAA' \
                'ACH5BAEAAAEALAAAAAAPAA0AAAMyGCHM+lAMMoeAT9Jtm5NDKI4Wo' \
                'FXcJphhipanq7Kvu8b1dLc5tcuom2foAQQAyKRSmQAAOw==')
        else:
            self.collapsed_icon=collapsed_icon
        if regular_icon == None:
            self.regular_icon=PhotoImage(
                data='R0lGODlhCwAOAJEAAAAAAICAgP///8DAwCH5BAEAAAMALAAA' \
                'AAALAA4AAAIphA+jA+JuVgtUtMQePJlWCgSN9oSTV5lkKQpo2q5W+' \
                'wbzuJrIHgw1WgAAOw==')
        else:
            self.regular_icon=regular_icon
        if plus_icon == None:
            self.plus_icon=PhotoImage(
                data='R0lGODdhCQAJAPEAAAAAAH9/f////wAAACwAAAAACQAJAAAC' \
                'FIyPoiu2sJyCyoF7W3hxz850CFIA\nADs=')
        else:
            self.plus_icon=plus_icon
        if minus_icon == None:
            self.minus_icon=PhotoImage(
                data='R0lGODdhCQAJAPEAAAAAAH9/f////wAAACwAAAAACQAJAAAC' \
                'EYyPoivG614LAlg7ZZbxoR8UADs=')
        else:
            self.minus_icon=minus_icon
        # horizontal distance that subtrees are indented
        self.dist_x=dist_x
        # vertical distance between rows
        self.dist_y=dist_y
        # how far to offset text label
        self.text_offset=text_offset
        # flag controlling connecting line display
        self.line_flag=line_flag
        # called just before subtree expand/collapse
        self.get_contents_callback=get_contents_callback
        # called after drag'n'drop
        self.drop_callback=drop_callback
        # create root node to get the ball rolling
        self.root=node_class(parent_node=None, label=root_label,
                             id=root_id, expandable_flag=1,
                             collapsed_icon=self.collapsed_icon,
                             expanded_icon=self.expanded_icon,
                             x=dist_x, y=dist_y, parent_widget=self)
        # configure for scrollbar(s)
        x1, y1, x2, y2=self.bbox('all') 
        self.configure(scrollregion=(x1, y1, x2+5, y2+5))
        # add a cursor
        self.cursor_box=self.create_rectangle(0, 0, 0, 0)
        self.move_cursor(self.root)
        # make it easy to point to control
        self.bind('<Enter>', self.PVT_mousefocus)
        # totally arbitrary yet hopefully intuitive default keybindings
        # stole 'em from ones used by microsoft tree control
        # page-up/page-down
        self.bind('<Next>', self.pagedown)
        self.bind('<Prior>', self.pageup)
        # arrow-up/arrow-down
        self.bind('<Down>', self.next)
        self.bind('<Up>', self.prev)
        # arrow-left/arrow-right
        self.bind('<Left>', self.ascend)
        # (hold this down and you expand the entire tree)
        self.bind('<Right>', self.descend)
        # home/end
        self.bind('<Home>', self.first)
        self.bind('<End>', self.last)
        # space bar
        self.bind('<Key-space>', self.toggle)

    # ----- PRIVATE METHODS (prefixed with "PVT_") -----
    # these methods are subject to change, so please try not to use them
    #
    # soak up event argument when moused-over
    def PVT_mousefocus(self, event):
        self.focus_set()
        
    # ----- PUBLIC METHODS -----
    # keep track of callback bindings so we can delete them later
    # I shouldn't have to do this!!!!
    def tag_bind(self, tag, seq, *args, **kw_args):
        # pass args to superclass
        func_id=apply(Canvas.tag_bind, (self, tag, seq)+args, kw_args)
        # save references
        self.bindings[tag]=self.bindings.get(tag, [])+[(seq, func_id)]

    # add contents for a node to list
    def add_list(self, list=None, name=None, id=None, flag=0,
                 expanded_icon=None, collapsed_icon=None):
        n=Struct()
        n.name=name
        n.id=id
        n.flag=flag
        if collapsed_icon:
            n.collapsed_icon=collapsed_icon
        else:
            if flag:
                # it's expandable, use closed folder icon
                n.collapsed_icon=self.collapsed_icon
            else:
                # it's not expandable, use regular file icon
                n.collapsed_icon=self.regular_icon
        if flag:
            if expanded_icon:
                n.expanded_icon=expanded_icon
            else:
                n.expanded_icon=self.expanded_icon
        else:
            # not expandable, don't need an icon
            n.expanded_icon=None
        if list == None:
            list=[]
        list.append(n)
        return list

    # add a node during get_contents_callback()
    def add_node(self, name=None, id=None, flag=0, expanded_icon=None,
                 collapsed_icon=None):
        self.add_list(self.new_nodes, name, id, flag, expanded_icon,
                      collapsed_icon)

    # search for a node
    def find_full_id(self, search):
        return self.root.PVT_find(search)
    
    # return node under cursor
    def cursor_node(self, search):
        return self.pos
        
    # scroll (in a series of nudges) so items are visible
    def see(self, *items):
        x1, y1, x2, y2=apply(self.bbox, items)
        while x2 > self.canvasx(0)+self.winfo_width():
            old=self.canvasx(0)
            self.xview('scroll', 1, 'units')
            # avoid endless loop if we can't scroll
            if old == self.canvasx(0):
                break
        while y2 > self.canvasy(0)+self.winfo_height():
            old=self.canvasy(0)
            self.yview('scroll', 1, 'units')
            if old == self.canvasy(0):
                break
        # done in this order to ensure upper-left of object is visible
        while x1 < self.canvasx(0):
            old=self.canvasx(0)
            self.xview('scroll', -1, 'units')
            if old == self.canvasx(0):
                break
        while y1 < self.canvasy(0):
            old=self.canvasy(0)
            self.yview('scroll', -1, 'units')
            if old == self.canvasy(0):
                break
            
    # move cursor to node
    def move_cursor(self, node):
        self.pos=node
        x1, y1, x2, y2=self.bbox(node.symbol, node.label)
        self.coords(self.cursor_box, x1-1, y1-1, x2+1, y2+1)
        self.see(node.symbol, node.label)
    
    # expand/close subtree
    def toggle(self, event=None):
        self.pos.toggle_state()

    # move to next lower visible node
    def next(self, event=None):
        self.move_cursor(self.pos.next_visible())
            
    # move to next higher visible node
    def prev(self, event=None):
        self.move_cursor(self.pos.prev_visible())

    # move to immediate parent
    def ascend(self, event=None):
        if self.pos.parent_node:
            # move to parent
            self.move_cursor(self.pos.parent_node)

    # move right, expanding as we go
    def descend(self, event=None):
        if self.pos.expandable_flag:
            self.pos.expand()
            if self.pos.child_nodes:
                # move to first subnode
                self.move_cursor(self.pos.child_nodes[0])
                return
        # if no subnodes, move to next sibling
        self.next()

    # go to root
    def first(self, event=None):
        # move to root node
        self.move_cursor(self.root)

    # go to last visible node
    def last(self, event=None):
        # move to bottom-most node
        self.move_cursor(self.root.PVT_last())

    # previous page
    def pageup(self, event=None):
        n=self.pos
        j=self.winfo_height()/self.dist_y
        for i in range(j-3):
            n=n.prev_visible()
        self.yview('scroll', -1, 'pages')
        self.move_cursor(n)

    # next page
    def pagedown(self, event=None):
        n=self.pos
        j=self.winfo_height()/self.dist_y
        for i in range(j-3):
            n=n.next_visible()
        self.yview('scroll', 1, 'pages')
        self.move_cursor(n)
        
    # ----- functions for drag'n'drop support -----
    # determine drag location in canvas coordinates
    # event.x & event.y don't seem to be what we want
    def where(self, event):
        # where the corner of the canvas is relative to the screen:
        x_org=self.winfo_rootx()
        y_org=self.winfo_rooty()
        # where the pointer is relative to the canvas widget,
        # including scrolling
        x=self.canvasx(event.x_root-x_org)
        y=self.canvasy(event.y_root-y_org)
        return x, y
    
    # accept dnd messages
    # i.e. we're a legit drop target, and we do implement d&d functions
    def dnd_accept(self, source, event):
        self.target=None
        return self

    # get ready to drag or drag has entered widget (create drag object)
    def dnd_enter(self, source, event):
        # this flag lets us know there's been drag motion
        self.drag=1
        x, y=self.where(event)
        x1, y1, x2, y2=source.widget.bbox(source.symbol, source.label)
        dx, dy=x2-x1, y2-y1
        # create dragging icon
        if source.expanded_flag:
            self.dnd_symbol=self.create_image(x, y,
                                              image=source.expanded_icon)
        else:
            self.dnd_symbol=self.create_image(x, y,
                                              image=source.collapsed_icon)
        self.dnd_label=self.create_text(x+self.text_offset, y, 
                                        text=source.get_label(),
                                        justify='left',
                                        anchor='w')

    # move drag icon
    def dnd_motion(self, source, event):
        # gets called A LOT, so no carriage return
        self.drag=1
        x, y=self.where(event)
        x1, y1, x2, y2=self.bbox(self.dnd_symbol, self.dnd_label)
        self.move(self.dnd_symbol, x-x1+source.x_off, y-y1+source.y_off)
        self.move(self.dnd_label, x-x1+source.x_off, y-y1+source.y_off)

    # finish dragging or drag has left widget (destroy drag object)
    def dnd_leave(self, source, event):
        self.delete(self.dnd_symbol)
        self.delete(self.dnd_label)

    # object has been dropped here
    def dnd_commit(self, source, event):
        # call our own dnd_leave() to clean up
        self.dnd_leave(source, event)
        # process pending events to detect target node
        # update_idletasks() doesn't do the trick if source & target are
        # on  different widgets
        self.update()
        if not self.target:
            # no target node
            return
        # we must update data structures based on the drop
        if self.drop_callback:
            try:
                # called with dragged node and target node
                # this is where a file manager would move the actual file
                # it must also move the nodes around as it wishes
                self.drop_callback(source, self.target)
            except:
                report_callback_exception()

#------------------------------------------------------------------------------
# the good 'ol test/demo code
if __name__ == '__main__':
    import os
    import sys

    # default routine to get contents of subtree
    # supply this for a different type of app
    # argument is the node object being expanded
    # should call add_node()
    def get_contents(node):
        path=apply(os.path.join, node.full_id())
        for filename in os.listdir(path):
            full=os.path.join(path, filename)
            name=filename
            folder=0
            if os.path.isdir(full):
                # it's a directory
                folder=1
            elif not os.path.isfile(full):
                # but it's not a file
                name=name+' (special)'
            if os.path.islink(full):
                # it's a link
                name=name+' (link to '+os.readlink(full)+')'
            node.widget.add_node(name=name, id=filename, flag=folder)

    root=Tk()
    root.title(os.path.basename(sys.argv[0]))
    tree=os.sep
    if sys.platform == 'win32':
        # we could call the root "My Computer" and mess with get_contents()
        # to return "A:", "B:", "C:", ... etc. as it's children, but that
        # would just be terminally cute and I'd have to shoot myself
        tree='C:'+os.sep

    # create the control
    t=Tree(master=root,
           root_id=tree,
           root_label=tree,
           get_contents_callback=get_contents,
           width=300)
    t.grid(row=0, column=0, sticky='nsew')

    # make expandable
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # add scrollbars
    sb=Scrollbar(root)
    sb.grid(row=0, column=1, sticky='ns')
    t.configure(yscrollcommand=sb.set)
    sb.configure(command=t.yview)

    sb=Scrollbar(root, orient=HORIZONTAL)
    sb.grid(row=1, column=0, sticky='ew')
    t.configure(xscrollcommand=sb.set)
    sb.configure(command=t.xview)

    # must get focus so keys work for demo
    t.focus_set()

    # we could do without this, but it's nice and friendly to have
    Button(root, text='Quit', command=root.quit).grid(row=2, column=0,
                                                      columnspan=2)

    # expand out the root
    t.root.expand()
    
    root.mainloop()
