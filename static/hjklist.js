var root;
var rootNode;
var selectedNode;
var converter = new Markdown.Converter().makeHtml;

var Item = Backbone.Model.extend({
    idAttribute: "_id",
    url: function() { 
        if (this.get('_id'))
            return "/" + this.get('_id');
        else
            return "/new";
    },
    initialize: function() {
        if (!this.get('items')) this.set({'items': new Items()});
        else this.set({'items': new Items(this.get('items'))});
    },
    parse: function(response) {
        response['items'] = new Items(response['items']);
        return response;
    },
});

var Items = Backbone.Collection.extend({
    model: Item,
});

var ItemView = Backbone.View.extend({
    events: {
        'click': 'selectAndGrow',
        'submit form.new': 'addChild',
        'submit form.edit': 'doUpdate',
    },
    initialize: function(options) {
        _.bindAll(this);
        this.el = h(
            'div',
            {class: 'item', id: this.model.get('_id')},
            [
                h('div', {class: 'content'}, [ ]),
            ]
        );
        this.$el = $(this.el);
        this.$newForm = $(h('form', {action: this.model.url() + '/add', class:'new'},
            [h('input', {type: 'text', name: 'name'})]));
        this.$editForm = $(h('form', {action: this.model.url() + '/add', class:'edit'},
            [h('input', {type: 'text', name: 'name'})]));
        this.$name = $(h('div', {class: 'name'}));
        this.$items = $(h('div', {class: 'items'}));
        this.$name.appendTo(this.$el.children('.content').first());
        this.$editForm.appendTo(this.$el.children('.content').first());
        this.$items.appendTo(this.$el);
        this.$newForm.appendTo(this.$el);
        this.model.bind('change', this.render, this);
        this.model.bind('destroy', this.remove, this);
        if (options.parent) this.parent = options.parent;
        this.children = [];
    },
    addItem: function(new_item) {
        var new_item_view = new ItemView({model: new_item, parent: this});
        this.children.push(new_item_view);
        this.$items.append(new_item_view.render().$el);
    },
    render: function() {
        var self = this;
        if (this.model.get('items').length) {
            this.$el.addClass('expandable');
            this.expandable = true;
        } else {
            this.expandable = false;
        }
        var name = this.model.get('name');
        var name_rep;
        if (['.png','.jpg','.gif'].indexOf(name.substr(-4)) != -1) name_rep = h('img', {src: name});
        else if (name.substr(0,7) == 'http://') name_rep = h('a', {href: name}, name);
        else name_rep = converter(name);
        this.$name.html(name_rep);
        this.$(".attributes").first().empty();
        this.$items.empty();
        this.$newForm.children('input[name="name"]').bind('keydown', 'esc', self.hideNewForm);
        this.$editForm.children('input[name="name"]').bind('keydown', 'esc', self.hideEditForm);
        this.children = [];
        _.each(this.model.get('items').models, function(new_item) {
            self.addItem(new_item);
        });
        if (this == rootNode) select_node(this.children[0]);
        return this;
    },
    addChild: function(e) {
        e.preventDefault();
        e.stopPropagation();
        var new_name = this.$newForm.children('input[name="name"]').val();
        var new_item = new Item({name: new_name, from_:this.model.id});
        new_item.save();
        this.model.get('items').add(new_item);
        this.render();
        this.expand();
        this.hideNewForm();
        this.showNewForm();
    },
    expand: function() {
        if (!this.grown) {
            this.model.fetch();
            this.grown = true;
        }
        $(this.el).addClass('expanded');
        this.$items.slideDown(200);
        this.expanded = true;
    },
    unexpand: function() {
        $(this.el).removeClass('expanded');
        this.$items.slideUp(200);
        this.expanded = false;
    },
    select: function(e) {
        e.stopPropagation();
        e.preventDefault();
        select_node(this);
    },
    grow: function(e) {
        e.stopPropagation();
        e.preventDefault();
        if (this.$el.hasClass('expanded')) {
            this.unexpand();
        } else {
            this.expand();
        }
    },
    selectAndGrow: function(e) {
        e.stopPropagation();
        e.preventDefault();
        if (this.$el.hasClass('expanded')) {
            if (this.$el.hasClass('selected')) {
                this.unexpand();
            }
        } else {
            this.expand();
        }
        select_node(this);
    },
    showNewForm: function() {
        if (!$(this.el).hasClass('expanded')) 
            this.expand();
        this.$newForm.show();
        this.$newForm.children('input[name="name"]').focus();
    },
    hideNewForm: function() {
        this.$newForm.children('input[name="name"]').val('');
        this.$newForm.children('input[name="name"]').blur();
        this.$newForm.hide();
    },
    showEditForm: function() {
        this.$editForm.children('input[name="name"]').val(this.model.get('name'));
        this.$editForm.children('input[name="name"]').focus();
        this.$editForm.show();
        this.$name.hide();
        this.$editForm.children('input[name="name"]').focus();
    },
    hideEditForm: function() {
        this.$editForm.children('input[name="name"]').val('');
        this.$editForm.children('input[name="name"]').blur();
        this.$name.show();
        this.$editForm.hide();
    },
    doUpdate: function(e) {
        e.preventDefault();
        e.stopPropagation();
        var new_name = this.$editForm.children('input[name="name"]').val();
        this.model.set({name: new_name});
        this.model.save();
        this.hideEditForm();
    },
    update: function() {
        this.model.fetch();
    },
    clear: function() {
        this.model.destroy();
    },
    remove: function() {
        this.parent.children = _.without(this.parent.children, this);
        $(this.el).remove();
    },
});

function select_node(node_view) {
    selectedNode.hideNewForm();
    $('.selected').removeClass('selected');
    $(node_view.el).addClass('selected');
    selectedNode = node_view;
    var from_top = selectedNode.$el.offset().top;
    var window_height = $(window).height();
    var scroll_top = document.body.scrollTop;
    if (from_top + 30 > (window_height + scroll_top)) document.body.scrollTop = from_top - window_height + 40;
    if (from_top < (scroll_top)) document.body.scrollTop = from_top - 10;
}

function move_left() {
    if (selectedNode.expanded && selectedNode != rootNode) selectedNode.unexpand();
    else {
        //if (selectedNode.parent == rootNode) return;
        select_node(selectedNode.parent);
    }
}
function move_down(go_inner) {
    go_inner = typeof go_inner !== 'undefined' ? go_inner : true;
    if (selectedNode.expanded && go_inner) {
        move_right();
    } else {
        var select_pos = selectedNode.parent.children.indexOf(selectedNode);
        if ((select_pos + 1) < selectedNode.parent.children.length) {
            select_node(selectedNode.parent.children[select_pos + 1]);
        } else {
            select_node(selectedNode.parent);
            move_down(false);
        }
    }
}
function move_far_down(go_inner) {
    go_inner = typeof go_inner !== 'undefined' ? go_inner : true;
    if (selectedNode.expanded && go_inner) {
        move_right();
        move_far_down();
    } else {
        var select_pos = selectedNode.parent.children.indexOf(selectedNode);
        if ((select_pos + 1) < selectedNode.parent.children.length) {
            select_node(selectedNode.parent.children[selectedNode.parent.children.length-1]);
        } else {
            select_node(selectedNode.parent);
            move_down(false);
        }
    }
}
function find_deepest_child(from_node) {
    if (from_node.expanded) {
        return find_deepest_child(_.last(from_node.children));
    } else { return from_node; }
}
function find_up_node(from_node) {
    var select_pos = from_node.parent.children.indexOf(from_node);
    if ((select_pos) > 0) {
        var up_node = from_node.parent.children[select_pos - 1];
        return find_deepest_child(up_node);
    } else {
        if (from_node.parent == rootNode) return find_deepest_child(rootNode);
        return from_node.parent;
    }
}
function find_far_up_node(from_node) {
    var select_pos = from_node.parent.children.indexOf(from_node);
    if ((select_pos) > 0) {
        var up_node = from_node.parent.children[0];
        return find_deepest_child(up_node);
    } else {
        if (from_node.parent == rootNode) return find_deepest_child(rootNode);
        return from_node.parent;
    }
}
function move_up() {
    select_node(find_up_node(selectedNode));
}
function move_far_up() {
    select_node(find_far_up_node(selectedNode));
}
function move_right() {
    if (selectedNode.expandable) {
        if (!selectedNode.expanded) selectedNode.expand();
        else select_node(selectedNode.children[0]);
    }
}
function new_child_node(e) {
    e.preventDefault();
    e.stopPropagation();
    selectedNode.showNewForm();
}
function new_below_node(e) {
    e.preventDefault();
    e.stopPropagation();
    selectedNode.parent.showNewForm();
}
function edit_node(e) {
    e.preventDefault();
    e.stopPropagation();
    selectedNode.showEditForm();
    console.log('editing?')
}

$(function() {
    //$("body").click(function(e) { return false; });
    $(document).bind('keydown', 'h', move_left);
    $(document).bind('keydown', 'j', move_down);
    $(document).bind('keydown', 'shift+j', move_far_down);
    $(document).bind('keydown', 'k', move_up);
    $(document).bind('keydown', 'shift+k', move_far_up);
    $(document).bind('keydown', 'l', move_right);
    $(document).bind('keydown', 'a', new_child_node);
    $(document).bind('keydown', 'o', new_below_node);
    $(document).bind('keydown', 'c', edit_node);
    $(document).bind('keydown', 'return', new_child_node);
    $(document).bind('keydown', 'backspace', function(e) {
        if (!$('input:focus').length) {
            e.preventDefault();
            e.stopPropagation();
            var up_node = find_up_node(selectedNode);
            selectedNode.clear();
            select_node(up_node);
            selectedNode.update();
        }
    });
});


