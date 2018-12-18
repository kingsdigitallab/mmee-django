var photo_search = function(g_initial_query) {

    /*
    notations:
        
        g_X : variable shared among all functions
        $X  : a jquery element  
    */

    // constents
    var g_image_size_increment = 75;
    var g_image_size_max = 500;
    var g_map_image_size = 2 * g_image_size_increment;

    // dependencies 
    var L = window.L;
    var Vue = window.Vue;
    var console = window.console;
    var mmee = window.mmee;

    // create the leaflet map on the web page
    var g_leaflet = window.search_map(L, g_map_image_size, function() {
        if (!window.$map) {
            window.$map = $('#map-leaflet').detach();
            // $('#photo-map').append($map);
            $('#sticky-map').append(window.$map);
        }
    });
        
    // the Vue.js logic for the whole search interface
    var g_search_app = new Vue({
        el: '#search-screen',
        data: {
            // the response from the photo Web API, a list of photos data
            photos: [],
            last_geo_query_hash: null,
            meta: {
                // the parameters of the search
                // they map directly to the Web API and the web page querystring
                query: g_initial_query,
                pagination: {},
                qs: '',
                facets: {},
            },
            links: {},
            searching: 1,
            // The tabs / views for fisplaying the results
            views: [
                {
                    id: 'tab1',
                    label: 'Grid',
                    key: 'grid',
                    class: 'fas fa-th',
                },
                {
                    id: 'tab2',
                    label: 'List',
                    key: 'list',
                    class: 'fas fa-list',
                },
                {
                    id: 'tab3',
                    label: 'Map',
                    key: 'map',
                    class: 'fas fa-map-marker-alt',
                },
            ]
        },
        mounted: function() {
            this.$nextTick(function () {
                // this is to fetch and show initial results
                this.call_api();
            });
        },
        watch: {
            'meta.query.order': function() {
                this.call_api({page: 1});
            },
            'meta.query.perpage': function() {
                this.call_api({page: 1});
            },
            'meta.query.geo': function() {
                if (this.meta.query.order == 'nearest') {
                    this.call_api({page: 1});
                }
            },
            'meta.query.view': function() {
                // do things in next tick to make sure vue's redrawn with map 
                this.$nextTick(function () {
                    // this is to show initial results
                    if (this.meta.query.view == 'map') {
                        this.resize_map();                    
                    }
                    this.call_api();
                });
            }
        },
        computed: {
            link_first: function() {
                return this.get_html_link_from_api_link(this.links.first);
            },
            link_last: function() {
                return this.get_html_link_from_api_link(this.links.last);                
            },
            link_next: function() {
                return this.get_html_link_from_api_link(this.links.next);                
            },
            link_prev: function() {
                return this.get_html_link_from_api_link(this.links.prev);
            },
        },
        methods: {
            is_map_on_page: function() {
                // on desktop the map is always on page
                // on mobile only if map view is selected
                // this will depends on the selected view and the display device
                return $('#photo-map').is(':visible');
            },
            on_change_option: function(option, event) {
                option[4] = event.target.checked ? 1: 0;
                this.call_api({page: 1});
            },
            on_phrase_submit: function() {
                // don't use a 'watch: phrase' otherwise all keydown will
                // generate a new query. 
                this.call_api({page: 1, facets: ''});
            },
            on_click_link: function(event, load_more) {
                // we call the api with the query string from the clicked hyperlink
                // to avoid doing a page reload.
                this.call_api({}, event.target.getAttribute('href'), load_more); 
            },
            get_html_link_from_api_link: function(link) {
                return link ? link.replace(/[^?]+[?]?/, '?') : '';
            },
            resize_map: function() {
                g_leaflet.resize_map();
            },
            show_map_bounds: function(bounds) {
                if (!this.is_map_on_page()) {
                    this.meta.query.view = 'map';
                }
                g_leaflet.fit_bounds(bounds);
            },
            call_api: function(aquery, query_string, load_more) {
                /*
                Calls the API with parameters found in this.meta.query.
                
                If aquery is provided, its parameters will override 
                this.meta.query.
                
                If query_string is provided (?page=1), it will be used instead
                of this.data.query and aquery.
                
                this.data is updated with the API response. Including this.meta.query.
                
                IMPORTANT: this function makes up to two requests to the API:
                
                * One request for the showing a paginated list of images
                
                * Another optional request for showing all (i.e. unpaginated) the photo markers on the map.
                
                Both are query dependent (i.e. depend on search phrase, facets).
                */
                
                var self = this;
                var query = {};
                self.searching = 1;
                
                if (query_string) {
                    query = mmee.get_dict_from_query_string(query_string);
                } else {
                    query_string = '';
                                        
                    query = $.extend(
                        {}, // Important: without this {}, we get all the getters and setters from self.meta.query
                        self.meta.query,
                        {
                            facets: this.get_string_from_selected_facets(),
                        },
                        aquery
                    );
                }
                
                query.imgspecs = this.get_image_spec(3, g_image_size_increment);
                                
                // request for the photo result (list of images)
                var req = $.getJSON('/api/1.0/photos/', query);
                req.done(function(data) {
                    if (!load_more) {
                        Vue.set(self, 'photos', []);
                    }
                    Array.prototype.push.apply(self.photos, data.data);
                    self.updating_from_response = 1;
                    console.log('' + query.geo + ' -> ' + data.meta.query.geo);
                    // Vue.set(self, 'meta', data.meta);
                    Vue.set(self, 'links', data.links);
                    self.updating_from_response = 0;
                    
                    mmee.replace_query_string(data.meta.qs);
                    self.searching = 0;
                });

                // request for the map result (map markers)
                if (this.is_map_on_page()) {
                    query.page = 1;
                    query.perpage = 5000;
                    query.geo_only = 1;
                    var geo_query_hash = this.get_hash_from_geo_query(query);
                    if (geo_query_hash !== self.last_geo_query_hash) {
                        console.log('GEO ONLY QUERY');
                        var req_geo_only = $.getJSON('/api/1.0/photos/', query);
                        req_geo_only.done(function(data) {
                            self.last_geo_query_hash = self.get_hash_from_geo_query(data.meta.query);
                            g_leaflet.replace_markers(data.data, 1);
                        });
                    }
                }
            },
            get_string_from_selected_facets: function() {
                // returns a single string representing all selected facets
                var ret = [];
                $.each(this.meta.facets, function(i, facet) {
                    $.each(facet[1], function(j, option) {
                        if (option[4]) {
                            ret.push(option[0]+':'+option[1]);
                        }
                    });
                });
                return ret.join(';');
            },
            get_hash_from_geo_query: function(query) {
                // returns a string that uniquely identifies the geo query.
                // e.g. 'phrase=street&facets='
                // Used to prevent calling the API twice with the same query.
                var fields = ['phrase', 'facets'];
                var ret = fields.map(function(field) {
                    return field + '=' + (query[field] || '');
                }).join('&');
                return ret;
            },
            get_image_spec: function(image_per_row, size_step) {
                // returns fixed height spec
                // compatible with wagtail image format spec string

                // dynamic image size so it's optimal for mobile or desktop.
                image_per_row = mmee.get_arg_default(image_per_row, 3);
                // size_step helps to avoid all possible client width
                // creating their own thumbnails on the server side.
                // It helps reusing existing thumbs.
                size_step = mmee.get_arg_default(size_step, 75);
                var image_height = Math.ceil(($('#results').width()) / image_per_row / size_step) * size_step;
                if (image_height > g_image_size_max) {
                    image_height = g_image_size_max;
                }
                return 'height-' + image_height;
            }
        }
    });

    function set_query_centre_from_map_centre() {
        var centre = g_leaflet.map.getCenter();
        g_search_app.meta.query.geo = mmee.get_str_from_latlng(centre)+','+g_leaflet.map.getZoom();
        // console.log('set query centre: ' + g_search_app.meta.query.geo);
    }

    set_query_centre_from_map_centre();
    g_leaflet.map.on('moveend', function () {
        set_query_centre_from_map_centre();
    });
    
    var $g_btn_show_on_map = null;
    $('div.wrapper').on('mouseenter mouseleave', '.photo-image', function(e) {
        // photo image interactions.
        // hover on photo => show pin button on top
        // click pin button => focus the map on that photo's marker
        if (!$g_btn_show_on_map) {
            $g_btn_show_on_map = $('<a href="#" class="btn-show-on-map"><i class="fas fa-map-pin"></i></a>');
            $g_btn_show_on_map.on('click', function() {
                var geo = $(this).parents('.photo-image').data('geo').split(',');
                var bounds = L.latLngBounds([geo.map(function(v) {return parseFloat(v);})]);
                g_search_app.show_map_bounds(bounds);
                return false;
            });
        }
        if (e.type == 'mouseleave') {
            $g_btn_show_on_map.detach();
        } else {
            $(e.currentTarget).prepend($g_btn_show_on_map);
        }
    });

};
