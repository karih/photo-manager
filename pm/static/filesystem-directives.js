


app.directive('filesystem', ['$http', 'tree_toggle_collapse', function($http, tree_toggle_collapse) {
	return {
		restrict: "E",
		replace: true,
		scope: {
			value: "=",
			selectFunction: "="
		},
		link: function(scope, element, attrs) {
			scope.root = {name: '/', path:'/', children: [], collapsed: true, current: scope.value == "/"};
			scope.toggle_collapse = tree_toggle_collapse.collapse;

			scope.$watch("value", function() {
				var recurse = function(nodes) {
					angular.forEach(nodes, function(v) {
						v.current = (v.path === scope.value) ? true : false;
						if (v.children.length > 0)
							recurse(v.children);
					});
				};

				scope.root.current = scope.value == "/" ? true : false;
				recurse(scope.root.children);
			});

			$http.get('/api/filesystem').success(function(data) {
				console.log("got fs data");
				var recurse = function(tree, path, node_collapsed) {

					var children = [];

					angular.forEach(tree, function(v, k) {
						var subpath = path + "/" + k;
						var hidden = node_collapsed;
						var collapsed = true;
						var current = false;

						if (scope.value.substr(0, subpath.length) == subpath) {
							hidden = false;
							scope.root.collapsed = false;
							if (scope.value.length > subpath.length) {
								console.log(subpath)
								collapsed = false;
							}
						}

						if (scope.value == subpath) {
							current = true;
						}

						var children_inner = recurse(v, subpath, collapsed);
						if (children_inner.length == 0) {
							collapsed = null;
						}

						children.push({name: k, path: subpath, hidden: hidden, collapsed: collapsed, current: current, children: children_inner}); 
					});

					return children;
				}

				scope.root.children = recurse(data.filesystem, "", true);
			})
		}, 
		templateUrl: "/static/partials/common/filesystem.html"
	}
}]);


app.factory('tree_toggle_collapse', function() {
	var collapse = function(event, node, collapsing) {
		if (node.children.length > 0) {
			if (typeof collapsing === "undefined") {
				console.log(node.path);
				collapsing = (node.collapsed === false);
			}

			node.collapsed = collapsing;
			angular.forEach(node.children, function(v, k) {
				v.hidden = collapsing;
				if (event.ctrlKey || collapsing) { collapse(event, v, collapsing); } 
			});
		}
	};
	return { collapse: collapse };
});


app.directive('fsnodes', function() {
	return {
		restrict: "E",
		replace: true,
		scope: {
			nodes: '=nodes',
			selectFunction: '='
		},
		template: "<ul><fsnode ng-repeat='value in nodes' node='value' select-function='selectFunction'></fsnode></ul>"
	}
});

app.directive('fsnode', ['tree_toggle_collapse', function(tree_toggle_collapse) {
	return {
		restrict: "E",
		replace: true,
		scope: {
			node: '=',
			selectFunction: '=selectFunction'
		},
		templateUrl: '/static/partials/filesystem-node.html',
		link: function(scope, element, attrs) {
			scope.toggle_collapse = tree_toggle_collapse.collapse;
		}
	}
}]);

