;

// daguerre jQuery namespace
var daguerre = {
    "jQuery": grp.jQuery.noConflict(true),
    "area_containers": [],
};

daguerre.jQuery(function($){
    function Area(conf, container){
        var area = this;
        if (conf.x1 === undefined || conf.x2 === undefined || conf.y1 === undefined || conf.y2 === undefined) {
            throw "Missing coordinates for area.";
        };
        if (!conf.storage_path) {
            throw "Invalid storage path for area.";
        };
        area.save_url = container.ele.data('area-url');
        area.img = container.img;
        area.row = $('<tr></tr>');
        area.editing = false;

        area.delete_link = $('<a href="#">Delete</a>');
        area.delete_link_click = function(e){
            e.preventDefault();
            area.remove();
            container.imgInit();
        };

        area.save_link = $('<a href="#">Save</a>');
        area.save_link_click = function(e){
            e.preventDefault();
            area.editing = false;
            // Fetch the name/priority values.
            area.name = area.row.find('input').first().val();
            area.priority = area.row.find('input').last().val();
            area.save();
            container.imgInit();
        };

        area.edit_link = $('<a href="#">Edit</a>');
        area.edit_link_click = function(e){
            e.preventDefault();
            $.each(container.areas, function(index, a){
                if (a.editing && !(a === area)) {
                    a.save_link.click()
                };
            });
            var parent = area.img.parent();
            area.img.imgAreaSelect({remove: true});
            area.img.imgAreaSelect({
                handles: true,
                parent: parent,
                x1: area.x1,
                y1: area.y1,
                x2: area.x2,
                y2: area.y2,
                persistent: true,
                onSelectChange: function(img, selection){
                    area.setSelection(selection);
                    area.display();
                },
                onSelectEnd: function(){},
                imageWidth: parent.data('width'),
                imageHeight: parent.data('height'),
            });
            area.editing = true;
            area.display()
        };

        area.display = function() {
            area.row.html('<td><input value="' + area.name + '" /></td>' +
                          '<td><input type="number" min=1 value="' + area.priority + '" /></td>' +
                          '<td>' + area.x1 + '</td>' +
                          '<td>' + area.y1 + '</td>' +
                          '<td>' + area.x2 + '</td>' +
                          '<td>' + area.y2 + '</td>' +
                          '<td class="edit-link"></td>' +
                          '<td></td>');
            area.row.children().last().html(area.delete_link);
            area.delete_link.click(area.delete_link_click)
            if (area.editing) {
                area.row.children('.edit-link').html(area.save_link);
                area.save_link.click(area.save_link_click);
            } else {
                area.row.children('.edit-link').html(area.edit_link);
                area.edit_link.click(area.edit_link_click);
                area.row.find('input').each(function(index, ele){
                    $(ele).focus(function(){
                        area.edit_link.click();
                        area.row.find('input').eq(index).focus();
                    });
                });
            };
        };

        area.setSelection = function(selection) {
            area.x1 = selection.x1;
            area.y1 = selection.y1;
            area.x2 = selection.x2;
            area.y2 = selection.y2;
        };

        area.init = function(conf) {
            area.setSelection(conf);
            area.priority = conf.priority || 3;
            area.name = conf.name || '';
            area.id = conf.id || null;
            area.storage_path = conf.storage_path;
            area.display()
        };
        area.init(conf);

        area.serialize = function(){
            return {
                x1: area.x1,
                y1: area.y1,
                x2: area.x2,
                y2: area.y2,
                priority: area.priority,
                name: area.name,
                id: area.id || '',
                storage_path: area.storage_path,
            }
        };

        area.save = function() {
            var url = area.save_url;
            if (area.id != null) {
                url += '/' + area.id;
            };
            $.post(url, area.serialize(), function(data){
                area.init(data);
            });
        };

        area.remove = function() {
            var url = area.save_url;
            if (area.id != null) {
                url += '/' + area.id;
                $.ajax(url, {type: 'DELETE'});
            };
            area.row.remove();
            var index = container.areas.indexOf(area);
            if (index != -1) {
                container.areas.splice(index, 1);
            };
        }
    };

    function AreaContainer(ele){
        var container = this,
            areas = container.areas = [],
            img = container.img = $('<img />'),
            add_link = container.add_link = $('<a class="add-another" href="#" title="Add Another"><img src="/static/admin/img/icon_addlink.gif" width="10" height="10" alt="Add Another"></a>'),
            table = container.table = $(
                '<table><thead><tr>' +
                '<th>Name</th>' +
                '<th>Priority</th>' +
                '<th>x1</th>' +
                '<th>y1</th>' +
                '<th>x2</th>' +
                '<th>y2</th>' +
                '<th></th>' +
                '<th>Delete</th>' +
                '</tr></thead><tbody></tbody></table>');

        container.ele = ele;
        container.ele.append(img);
        container.ele.append(table);
        table.find('tr').children().eq(-2).append(add_link);

        container.addArea = function(conf, activate) {
            var area = new Area(conf, container);
            areas.push(area);
            table.append(area.row);
            if (activate) {area.edit_link.click();};
        };

        container.imgInit = function() {
            container.img.imgAreaSelect({remove: true});
            container.img.imgAreaSelect({
                parent: ele,
                onSelectEnd: function(img, selection){
                    container.addArea({
                        x1: selection.x1,
                        y1: selection.y1,
                        x2: selection.x2,
                        y2: selection.y2,
                        storage_path: ele.data('storage-path'),
                    }, true);
                },
                imageWidth: ele.data('width'),
                imageHeight: ele.data('height'),
            });

        };

        container.init = function() {
            add_link.click(function(e){
                e.preventDefault();
                container.addArea({
                    storage_path: ele.data('storage-path'),
                    x1: 0,
                    y1: 0,
                    x2: ele.data('width'),
                    y2: ele.data('height'),
                }, true);
            });

            $.getJSON(ele.data('url'), {w: 400, max_h: 800, a: 'fit'}, function(data){
                img.attr('src', data['url']);
                img.attr('width', data['width']);
                img.attr('height', data['height']);
                container.imgInit()
            });
            $.getJSON(ele.data('area-url'), function(data){
                $.each(data, function(index, conf){
                    container.addArea(conf);
                });
            });
        };
        container.init()
    };
    $('.daguerre-areas').each(function(){
        daguerre.area_containers.push(new AreaContainer($(this)));
    });

    // Set csrf token on post requests.
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
});