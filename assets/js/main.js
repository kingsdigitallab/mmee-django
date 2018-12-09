$(function() {
    // Your JS Here
    

    
});

function format_geo(coord) {
    // format_geo(12.3456) == 12.34
    return parseFloat(Math.round(coord * 1000) / 1000).toFixed(3);
}

function get_str_from_latlng(latlng) {
    // latlng = {lat: 51.50922324175514, lng: -0.040082931518554694}
    // return '51.50,-0.04'
    return format_geo(latlng.lat) + ',' + format_geo(latlng.lng);    
}

