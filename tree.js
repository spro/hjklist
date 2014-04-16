var vent = _.extend({}, Backbone.Events);

var Item = Backbone.Model.extend({
    initialize: function() {

    },
});

var ItemView = Backbone.Model.extend({
    initialize: function() {
        this.el = h('div', {class: 'item'}, h('div', {class: 'content'}));
        this.$el = $(this.el);
    },
    render: function() {
        this.$('.content').html(this.model.get('content'));
        return this;
    },
});

