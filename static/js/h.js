/**
 * h(tagName, [attributes], [children])
 * Returns a dom element.
 * - tagName is obvious
 * - attributes is an object of the element's attributes: an attribute
 * can be a string, number, or boolean (does the right thing for booleans,
 * ie: {disabled:true} --> disabled="disabled" [not actually sure if
 * this is universal, but whatever])
 * - children can be DOM elements, strings, or numbers - and if there's
 * only one it doesn't have to be in a list
 */
function h(tagName, arg1, arg2) {
    var el = document.createElement(tagName);
    var attrs = {};
    var children = [];
    
    if(arg1!==undefined) {
        if (_.isArray(arg1)) {
            children = arg1;
        } else if (isChild(arg1)) {
            children = [arg1];
        } else {
            attrs = arg1;
        }
        
        if (arg2!==undefined) {
            children = isChild(arg2) ? [arg2] : arg2;
        }
    }
    
    _.each(attrs, function(value, name) {
        if (!_.isBoolean(value) || value) {
            value = coerceValue(value, name);
            if (value !== null) {
                var attr = document.createAttribute(name);
                attr.nodeValue = value;
                el.setAttributeNode(attr);
            }
        }
    });
    
    _.each(children, function(child){
        el.appendChild(handleChild(child));
    });
    
    return el;
}

// returns true if the thing can be a child
function isChild(x) {
    return _.isString(x) || _.isElement(x) || _.isNumber(x);
}

// makes child into a dom element
function handleChild(x) {
    if (_.isElement(x)) {
        return x;
    } else {
        return document.createTextNode(_.isNumber(x) ? x.toString() : x);
    }
}

//return String value for attribute, or null to remove the attribute
function coerceValue(value, name) {
    if(_.isString(value)) {
        return value;
    } else if (_.isNumber(value)) {
        return value.toString();
    } else {
        return (_.isBoolean(value) && value) ? name : null;
    }
}

// 2011 by i@pjmartel.com
// public domain
