$(function() {
    // Your JS Here
    
});

var mmee = (function() {
    var ns = {}; 
    
    ns.format_geo = function(coord) {
        // format_geo(12.3456) == 12.345
        return parseFloat(Math.round(coord * 1000) / 1000).toFixed(3);
    };
    
    ns.get_str_from_latlng = function(latlng) {
        // latlng = {lat: 51.50922324175514, lng: -0.040082931518554694}
        // return '51.50,-0.04'
        return ns.format_geo(latlng.lat) + ',' + ns.format_geo(latlng.lng);    
    };
    
    ns.replace_query_string = function(qs) {
        if (history.pushState) {
            var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + '?' + qs;
            window.history.pushState({path:newurl},'',newurl);
        }
    };

    ns.get_dict_from_query_string = function(qs) {
        // qs = '?a=b&c=d'
        var ret = {};

        // only keep the query string, without path or fragment
        qs = (qs || '').replace(/#.*$/, '');
        var idx = qs.indexOf('?');
        if (idx > -1) qs = qs.substring(idx + 1);

        // convert to dictionary / object
        qs.split('&').forEach(function(pair) {
            pair = pair.split('=');
            ret[pair[0]] = decodeURIComponent(pair[1] || '');
        });

        return ret;
    };

    ns.get_arg_default = function(arg, def) { 
        return typeof arg !== 'undefined' ? arg : def; 
    };
    
    return ns;
})();
