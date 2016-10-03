// https://stackoverflow.com/questions/12680296/using-bootstrap-typeahead-with-angular
app.directive('dirnameFacet', function() {
	return {
		restrict: "E",
		replace: true,
		scope: {
			title: "@",
			queryFunction: "&",
			value: "=",
			state: "="
		},
		controller: function($scope) {
			$scope.valueObj = {value: null};
			$scope.validObj = {valid: false};
			$scope.active = ($scope.value === null) ? false : true;
			$scope.query = $scope.value;
			$scope.valid = false;

			$scope.innerQueryFunction = function(query, callback) {
				//console.log("innerQueryFuction(", query, ", ", callback, ")");
				if (query === null || query === "" || query.length < 2) { query = "/"; }
				$scope.queryFunction({query: query, callback: function(response) { 
					//console.log("RASSS", response);
					callback(response); 
				}});
			}

			$scope.clear = function() { $scope.valueObj.value = "/"; $scope.value = null; };
		},
		link: function($scope, elements, attrs) {
			$scope.$watch('valueObj', function(new_value) {
				//console.log("dirnameFacet.valueObj(", new_value, ")");
				// typeahead has picked a new value
				if (new_value.value !== null && $scope.value !== new_value.value) {
					if (new_value.value.length < 2)
						$scope.value = null;
					else
						$scope.value = new_value.value;
				}
			}, true);

			$scope.$watch('value', function(new_value) {
				//console.log("dirnameFacet.value(", new_value, ")");
				$scope.query = ($scope.value === null || $scope.value.length < 2) ? "/" : $scope.value;
				$scope.active = ($scope.value === null || $scope.value.length < 2) ? false : true;
				if ($scope.valueObj.value !== new_value)
					$scope.valueObj.value = new_value;
			});
		},
		templateUrl: '/static/partials/common/dirname_facet.html'
	}
});


// https://stackoverflow.com/questions/12680296/using-bootstrap-typeahead-with-angular
app.directive('termFacet', function() {
	//console.log("termFacet()");
	return {
		restrict: "E",
		replace: true,
		scope: {
			title: "@",
			queryFunction: "&",
			value: "=",
			state: "=",
		},
		controller: function($scope) {
			$scope.valueObj = {value: null};
			$scope.validObj = {valid: false};
			$scope.all_candidates = null;
			$scope.null_candidates = null;
		},
		link: function($scope, element, attrs) {
			$scope.active = ($scope.value === null) ? false : true;
			$scope.query = $scope.value;

			$scope.innerQueryFunction = function(query, callback) {
				//console.log("termFacet(", $scope.title, ").query(", query, ", callback)");
				$scope.queryFunction({query: query, callback: function(response) { 
					//console.log("termFacet(", $scope.title, ").queryFunctionCallback(", response, ")");
					$scope.null_candidates = response.null;
					callback(response); 
				}});
			}

			$scope.clear = function() { $scope.valueObj.value = null; $scope.value = null; };

			$scope.$watch('valueObj', function(new_value) {
				//console.log("termFacet.$watch('valueObj', ", new_value, ")");
				// typeahead has picked a new value
				if (new_value.value !== null && $scope.value !== new_value.value) {
					if (new_value.value === "")
						$scope.value = null;
					else
						$scope.value = new_value.value;
				}
			}, true);

			$scope.$on('stateChangeSuccess', function(event) {
				//console.log("termFacet(", $scope.title, ").$scope.$on('stateChangeSuccess', ", event);
				$scope.innerQueryFunction($scope.value, function() {});
			});

			$scope.$watch('value', function(new_value) {
				//console.log("termFacet(", $scope.title, ").$watch('value', ", new_value, ")");
				//$scope.innerValue = new_value;
				$scope.query = ($scope.value === null) ? "" : $scope.value;
				$scope.active = ($scope.value === null) ? false : true;
				if ($scope.valueObj.value !== new_value)
					$scope.valueObj.value = new_value;
			}, true);

			$scope.choose = function(value) {
				//console.log("termFacet.choose(", value, ")");
				$scope.value = value;
			}

			$scope.$watch('state', function(new_value) {
				//console.log("termFacet(", $scope.title, ").$watch('state', " + new_value + ")");
				if ($scope.null_candidates === null) {
					$scope.innerQueryFunction($scope.value, function() {});
				}

				if (new_value == 2 && $scope.all_candidates === null) {
					$scope.all_candidates = [];
					$scope.queryFunction({query: null, callback: function(response) {
						angular.forEach(response.buckets, function(val) {
							$scope.all_candidates.push(val);
						});
						$scope.null_candidates = response.null;
					}});
				}
			});
		},
		templateUrl: '/static/partials/common/term_facet.html'
	}
});


app.directive('dateFacet', function() {
	return {
		restrict: "E",
		replace: true,
		scope: {
			title: "@",
			queryFunction: "&",
			value: "=",
			state: "=",
		},
		controller: function($scope) {
			$scope.null_candidates = null;
			$scope.years = [];
		},
		link: function($scope, element, attrs) {

			var expanded = function(values) {
				angular.forEach(values, function(val, key) {
					val.expanded = false;
					if (val.hasOwnProperty("months")) {
						val.months = expanded(val.months);
						angular.forEach(val.months, function(v, k) {
							if (v.selected || v.expanded)
								values[key].expanded = true;
						});
					} else if (val.hasOwnProperty("days")) {
						val.days = expanded(val.days);
						angular.forEach(val.days, function(v, k) {
							if (v.selected || v.expanded)
								values[key].expanded = true;
						});
					} 
					
					if (val.selected == true) {
						values[key].expanded = true;
					}
				});

				return values;
			}

			$scope.innerQueryFunction = function(query) {
				console.log("dateFacet.query(", query, ", callback)");

				$scope.queryFunction({query: query, callback: function(response) {
					$scope.null_candidates = response.null;
					$scope.years = expanded(response.years);
					console.log($scope.years);
				}});
			}

			$scope.choose = function(day_str) {
				if (day_str === $scope.value) {
					$scope.value = null;
				} else {
					$scope.value = day_str;
				}
			}

			$scope.clear = function() {
				$scope.value = null;
			}

			$scope.$watch('value', function(new_value) {
				console.log("dateFacet.$watch('value', ", new_value, ")");
				$scope.active = ($scope.value === null) ? false : true;
			}, true);

			$scope.$on('stateChangeSuccess', function(event) {
				console.log("dateFacet.$scope.$on('stateChangeSuccess', ", event);
				$scope.innerQueryFunction($scope.value, function() {});
			});

			$scope.$watch('state', function(new_value) {
				console.log("dateFacet.$watch('state', " + new_value + ")");
				if (new_value > 0) {
					if ($scope.null_candidates === null) {
						$scope.innerQueryFunction($scope.value, function(response) {
							angular.forEach(response.buckets, function(value) {
							});
						});
					}
				}
			});

			$scope.clear = function() { $scope.value = null; };
		},
		templateUrl: '/static/partials/common/date_facet.html'
	}
});


/*
app.directive('facet', function() {
	return {
		restrict: "E",
		replace: true,
		scope: { 
			name: "@", 
			options: "=",
			filter: "&",
			formatter: "=?",
			expanded: "=?"
		},
		controller: function($scope) {
			if (!angular.isDefined($scope.formatter)) { $scope.formatter = function(v) { return v; }; }
			if (!angular.isDefined($scope.expanded)) { $scope.expanded = false; }
			$scope.has_more = false;

			var item_count = 3;

			var update_visible = function() {
				if (angular.isDefined($scope.options) && $scope.options.length > item_count) {
					$scope.has_more = true;
				} else {
					$scope.has_more = false;
				}

				$scope.visible_options = [];
				angular.forEach($scope.options, function(val) {
					if (val.selected || $scope.visible_options.length < item_count || $scope.expanded) {
						$scope.visible_options.push(val);
					}
				});	

				if ($scope.expanded || !$scope.has_more) {
					$scope.visible_options.sort(function(a, b) { return a.value == b.value ? 0 : (a.value > b.value ? 1 : -1); });
				}
			}

			$scope.toggle = function() {
				$scope.expanded = !$scope.expanded;
				update_visible();
			}

			$scope.$watch('options', update_visible);
			
		},
		templateUrl: "/static/partials/common/facet.html"
	}
});
*/

// these is a bit of a shit-show, but basically the purpose is to manipulate the html so the active facet is at the bottom of the facets, in order for the float: left to operate correctly
app.directive('photoList', [function() {
	//console.log("photoList()");

	return {
		restrict: "A",
		replace: false,
		scope: false,
		link: function(scope, elements, attrs) {
			//console.log("photoList.link(", scope, ", ", elements, ", ", attrs, ")");
			element = elements[0];
			var facets = [];
			var dest = null;
			var from = null;
			scope.facet_ontop = null;

			angular.forEach(element.children, function(child, key) {
				if (child.classList.contains("facet")) {
					facets.push({key:key, element: child, state: child.getAttribute("state").substr(6), });
					if (scope.state[child.getAttribute("state").substr(6)] == 2) {
						from = key;
					}
					
				} else if (child.id == "photo-list") {
					dest = key;
				}
			});

			var moveToTop = function(key) {
				if (scope.facet_ontop !== null) {
					//console.log("ERRROR")
					return;
				}

				element.insertBefore(element.children[key], element.children[dest]);
				scope.facet_ontop = key;
			};	

			var clearTop = function() {
				if (scope.facet_ontop !== null) {
					element.insertBefore(element.children[dest-1], element.children[scope.facet_ontop]);
					scope.facet_ontop = null;
				}
			}

			if (from !== null)
				moveToTop(from);

			scope.$on('stateChangeSuccess', function(event, changedParams) { 
				clearTop();

				angular.forEach(facets, function(val) {
					if (scope.state[val.state] == 2) {
						moveToTop(val.key);
					}
				});
			});
		},
	}
}]);
